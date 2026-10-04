#!/usr/bin/env python3
"""
Turns a decomposition JSON file into files you can hand straight to Jira:

  * a CSV for Jira's bulk importer (Settings > System > External system import > CSV, or
    Project > Import work items in Jira Cloud) — one Epic plus one row per story, with
    descriptions in Jira wiki markup, labels, the epic as Parent, and "blocks" / "relates"
    links between stories;
  * a Markdown file with the same stories, for review or for pasting by hand.

Usage:
    python3 export_jira.py <data_json_path> [--csv PATH] [--md PATH] [options]

Options:
    --csv PATH            Write the Jira import CSV here.
    --md PATH             Write the Markdown stories here.
    --no-epic             Don't create an Epic row / Parent links.
    --epic-name TEXT      Epic summary (default: the project name).
    --type-map A=B        Map a decomposition story type to a Jira issue type, repeatable.
                          Defaults: Story/Technical Story/Enabler -> Story, Spike/Task -> Task,
                          Bug -> Bug. Use e.g. --type-map Spike=Spike if your project has it.
    --label TEXT          Extra label added to every row, repeatable.

When importing, map the columns as: Issue Id -> Issue Id, Parent -> Parent, Link "blocks" ->
the "Blocks" link type, Link "relates" -> the "Relates" link type. Every other column maps to
the field of the same name. Issue Ids are only used inside the file to wire up links.
"""
import argparse
import csv
import json
import os
import re
import sys

DEFAULT_TYPE_MAP = {
    "Story": "Story", "Technical Story": "Story", "Enabler": "Story",
    "Spike": "Task", "Task": "Task", "Bug": "Bug",
}
JIRA_DESCRIPTION_LIMIT = 32000  # Jira rejects descriptions over 32,767 characters


def _label(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(text).strip()).strip("-").lower()


def _wiki(text):
    """Escape characters Jira wiki markup would otherwise treat as macros or links."""
    return re.sub(r"([{}\[\]])", r"\\\1", str(text or ""))


def _api_text(api):
    if isinstance(api, str):
        return api
    head = " ".join(x for x in (api.get("method"), api.get("path")) if x)
    extra = "; ".join(f"{k}: {api[k]}" for k in ("request", "response", "auth") if api.get(k))
    return f"{head} ({extra})" if extra else head


def _lookups(data):
    reqs = {}
    for key in ("business_requirements", "functional_requirements", "non_functional_requirements"):
        for r in data.get(key, []) or []:
            reqs[r.get("id")] = r
    qs = {q.get("id"): q for q in data.get("open_questions", []) or []}
    rules = {r.get("id"): r for r in data.get("business_rules", []) or []}
    return reqs, qs, rules


def _story_questions(story, qs):
    ids = list(story.get("open_question_ids") or [])
    for q in qs.values():
        if story.get("id") in (q.get("story_ids") or []) and q.get("id") not in ids:
            ids.append(q.get("id"))
    return [qs[i] for i in ids if i in qs]


def _sections(story, data):
    """Yields (heading, kind, items) where kind is 'text' or 'list'. Shared by both outputs."""
    reqs, qs, rules = _lookups(data)
    tc = story.get("technical_context") or {}
    ui = tc.get("ui_spec") or {}
    testing = tc.get("testing") or {}
    yield "User story", "text", story.get("user_story")
    yield "Description", "text", story.get("description")
    yield "Why this is its own story", "text", story.get("decomposition_rationale")
    yield "Acceptance criteria", "ac", story.get("acceptance_criteria") or []
    yield "In scope", "list", story.get("in_scope") or []
    yield "Out of scope", "list", story.get("out_of_scope") or []
    yield "Business rules", "list", [f"{i}: {rules[i].get('text')}" if i in rules else i
                                     for i in story.get("business_rule_ids") or []]
    ui_items = []
    if ui.get("screen") and ui.get("screen") != "n/a":
        ui_items.append(f"Screen: {ui['screen']}")
        for k in ("components", "fields", "states"):
            if ui.get(k):
                ui_items.append(f"{k.capitalize()}: {', '.join(ui[k])}")
        for n in ui.get("navigates_to") or []:
            ui_items.append(f"Navigates to {n.get('to')} ({n.get('trigger') or 'no trigger given'})")
    yield "UI / UX", "list", ui_items
    yield "APIs", "list", [_api_text(a) for a in tc.get("apis") or []]
    tech = []
    for k, name in (("affected_systems", "Affected systems"), ("data", "Data"), ("security", "Security"), ("cicd", "CI/CD")):
        if tc.get(k):
            tech.append(f"{name}: {', '.join(tc[k])}")
    yield "Technical context", "list", tech
    yield "Testing", "list", [f"{k.upper() if k in ('api', 'e2e') else k.capitalize()}: {', '.join(testing[k])}"
                              for k in ("unit", "integration", "api", "e2e") if testing.get(k)]
    yield "Open questions", "list", [
        f"{q.get('id')} ({q.get('severity') or 'Unrated'}): {q.get('question')} — owner: {q.get('owner') or 'Unassigned'}"
        + (" — AI-identified" if q.get("origin") == "ai_identified" else "")
        for q in _story_questions(story, qs)]
    yield "Source requirements", "list", [
        f"{i}: {reqs[i].get('text')}" if i in reqs else i for i in story.get("source_requirement_ids") or []]
    yield "Dependencies", "list", [
        f"{(d.get('relationship') or '').replace('_', ' ')} {d.get('story_id')}" + (f" — {d.get('reason')}" if d.get("reason") else "")
        for d in story.get("dependencies") or []]


def wiki_description(story, data):
    out = []
    for heading, kind, items in _sections(story, data):
        if not items:
            continue
        out.append(f"h3. {heading}")
        if kind == "text":
            out.append(_wiki(items))
        elif kind == "ac":
            for i, ac in enumerate(items, 1):
                if isinstance(ac, str):
                    out.append(f"# {_wiki(ac)}")
                else:
                    out.append(f"# *Given* {_wiki(ac.get('given'))} *when* {_wiki(ac.get('when'))} "
                               f"*then* {_wiki(ac.get('then'))}")
        else:
            out.extend(f"* {_wiki(x)}" for x in items)
        out.append("")
    out.append(f"_Generated by jira-ticket-builder-skill from {story.get('id')}._")
    text = "\n".join(out)
    if len(text) > JIRA_DESCRIPTION_LIMIT:
        text = text[:JIRA_DESCRIPTION_LIMIT - 60] + "\n\n_(truncated — see the requirements portal for the rest)_"
    return text


def markdown(data):
    project = data.get("project") or {}
    lines = [f"# {project.get('name') or 'Stories'}", ""]
    if project.get("source_summary"):
        lines += [project["source_summary"], ""]
    for s in data.get("stories", []) or []:
        lines += [f"## {s.get('id')} — {s.get('title')}", "", f"**Type:** {s.get('type') or 'Story'}", ""]
        for heading, kind, items in _sections(s, data):
            if not items:
                continue
            lines.append(f"### {heading}")
            if kind == "text":
                lines.append(str(items))
            elif kind == "ac":
                for i, ac in enumerate(items, 1):
                    lines.append(f"{i}. {ac}" if isinstance(ac, str) else
                                 f"{i}. **Given** {ac.get('given')} **when** {ac.get('when')} **then** {ac.get('then')}")
            else:
                lines.extend(f"- {x}" for x in items)
            lines.append("")
        lines += ["---", ""]
    return "\n".join(lines)


def link_map(data):
    """Returns (blocks, relates): dicts story_id -> set of story_ids, in Jira's direction
    ('A blocks B' goes in A's row). depends_on is flipped: 'A depends on B' == 'B blocks A'."""
    ids = {s.get("id") for s in data.get("stories", []) or []}
    blocks, relates = {}, {}

    def add(table, a, b):
        if a in ids and b in ids and a != b:
            table.setdefault(a, set()).add(b)

    for s in data.get("stories", []) or []:
        for d in s.get("dependencies") or []:
            rel, other = d.get("relationship"), d.get("story_id")
            if rel == "depends_on":
                add(blocks, other, s.get("id"))
            elif rel == "blocks":
                add(blocks, s.get("id"), other)
            elif rel == "relates_to":
                if s.get("id") not in relates.get(other, set()):
                    add(relates, s.get("id"), other)
    for d in data.get("dependencies", []) or []:
        add(blocks, d.get("to"), d.get("from"))
    return blocks, relates


def csv_rows(data, epic=True, epic_name=None, type_map=None, extra_labels=()):
    type_map = {**DEFAULT_TYPE_MAP, **(type_map or {})}
    stories = data.get("stories", []) or []
    issue_id = {s.get("id"): str(i) for i, s in enumerate(stories, start=2 if epic else 1)}
    blocks, relates = link_map(data)
    _, qs, _ = _lookups(data)
    project = data.get("project") or {}

    rows = []
    if epic:
        rows.append({
            "Issue Id": "1", "Issue Type": "Epic", "Parent": "",
            "Summary": epic_name or project.get("name") or "Decomposed requirements",
            "Description": _wiki(project.get("source_summary") or ""),
            "Labels": [_label(l) for l in extra_labels], "blocks": [], "relates": [],
        })
    for s in stories:
        sid = s.get("id")
        labels = [_label(s.get("type") or "story"), _label(sid)] + [_label(l) for l in extra_labels]
        if s.get("business_capability"):
            labels.append(_label(s["business_capability"]))
        if any((q.get("severity") in ("Critical", "High")) for q in _story_questions(s, qs)):
            labels.append("needs-clarification")
        rows.append({
            "Issue Id": issue_id[sid],
            "Issue Type": type_map.get(s.get("type"), "Story"),
            "Parent": "1" if epic else "",
            "Summary": f"{s.get('title')}"[:254],
            "Description": wiki_description(s, data),
            "Labels": list(dict.fromkeys(l for l in labels if l)),
            "blocks": sorted(issue_id[x] for x in blocks.get(sid, ())),
            "relates": sorted(issue_id[x] for x in relates.get(sid, ())),
        })
    return rows


def write_csv(rows, path, epic=True):
    n_labels = max((len(r["Labels"]) for r in rows), default=0) or 1
    n_blocks = max((len(r["blocks"]) for r in rows), default=0)
    n_relates = max((len(r["relates"]) for r in rows), default=0)
    header = ["Issue Id", "Issue Type", "Summary", "Description"] + (["Parent"] if epic else []) \
        + ["Labels"] * n_labels + ['Link "blocks"'] * n_blocks + ['Link "relates"'] * n_relates
    pad = lambda xs, n: list(xs) + [""] * (n - len(xs))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([r["Issue Id"], r["Issue Type"], r["Summary"], r["Description"]]
                       + ([r["Parent"]] if epic else [])
                       + pad(r["Labels"], n_labels) + pad(r["blocks"], n_blocks) + pad(r["relates"], n_relates))


def main(argv=None):
    p = argparse.ArgumentParser(description="Export decomposition stories for Jira.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("data_json_path")
    p.add_argument("--csv", dest="csv_path", metavar="PATH")
    p.add_argument("--md", dest="md_path", metavar="PATH")
    p.add_argument("--no-epic", action="store_true")
    p.add_argument("--epic-name")
    p.add_argument("--type-map", action="append", default=[], metavar="A=B")
    p.add_argument("--label", action="append", default=[])
    a = p.parse_args(argv)
    if not (a.csv_path or a.md_path):
        p.error("give at least one of --csv or --md")
    type_map = {}
    for item in a.type_map:
        if "=" not in item:
            p.error(f"--type-map expects A=B, got {item!r}")
        k, v = item.split("=", 1)
        type_map[k.strip()] = v.strip()

    with open(a.data_json_path, encoding="utf-8") as f:
        data = json.load(f)
    n = len(data.get("stories", []) or [])
    if a.csv_path:
        rows = csv_rows(data, epic=not a.no_epic, epic_name=a.epic_name, type_map=type_map, extra_labels=a.label)
        write_csv(rows, a.csv_path, epic=not a.no_epic)
        links = sum(len(r["blocks"]) + len(r["relates"]) for r in rows)
        print(f"  wrote {a.csv_path} ({n} stories{', 1 epic' if not a.no_epic else ''}, {links} links)")
    if a.md_path:
        with open(a.md_path, "w", encoding="utf-8") as f:
            f.write(markdown(data))
        print(f"  wrote {a.md_path} ({n} stories)")


if __name__ == "__main__":
    main()
