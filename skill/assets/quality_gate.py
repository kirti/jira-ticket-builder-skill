#!/usr/bin/env python3
"""
Runs the D5 quality gate against a decomposition JSON file and reports pass/fail per check.
Run this before generating the portal — don't re-derive these checks ad hoc each time; that has
produced the same class of bug (an open question's story_ids pointing at a story that doesn't
list the question back in its own open_question_ids) on every decomposition run tested so far.

Usage:
    python3 quality_gate.py <data_json_path> [--json]

    --json   Print a machine-readable report (checks, problems, computed readiness) instead of text.

Exits non-zero if any FAIL-level check fails, so it can be used as a hard gate in a script.
WARN-level checks are reported but never fail the gate.

Also importable: compute_readiness(data), story_completeness(story, data) and apply_computed(data)
are used by build_portal.py so the portal's percentages come from the data, not from estimates.
"""
import copy
import json
import os
import re
import sys

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decomposition.schema.json")
REQ_KEYS = ("business_requirements", "functional_requirements", "non_functional_requirements")
CLOSED_STATUSES = {"resolved", "closed", "answered", "done"}
MAX_SHOWN = 8


# ---------------------------------------------------------------- schema validation
_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate_schema(value, schema, path="$"):
    """Minimal JSON Schema validator (type, required, properties, items, enum, pattern,
    minimum, maximum, minLength) — enough for decomposition.schema.json, no dependencies."""
    errors = []
    types = schema.get("type")
    if types:
        types = types if isinstance(types, list) else [types]
        if not any(_TYPES[t](value) for t in types):
            return [f"{path}: expected {' or '.join(types)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: must not be empty")
    if _TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field '{key}'")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                errors.extend(validate_schema(value[key], sub, f"{path}.{key}"))
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(validate_schema(item, schema["items"], f"{path}[{i}]"))
    return errors


# ---------------------------------------------------------------- computed metrics
def _reqs(data):
    return [r for k in REQ_KEYS for r in data.get(k, []) or []]


def _pct(n, d):
    return round(100 * n / d) if d else 0


def _has_tests(story):
    t = (story.get("technical_context") or {}).get("testing") or {}
    return any(t.get(k) for k in ("unit", "integration", "api", "e2e"))


def _has_tech(story):
    tc = story.get("technical_context") or {}
    return bool(tc.get("affected_systems") or tc.get("apis"))


def _blocking_questions(story, data):
    ids = set(story.get("open_question_ids") or [])
    return [q for q in data.get("open_questions", []) or []
            if (q.get("id") in ids or story.get("id") in (q.get("story_ids") or []))
            and q.get("severity") in ("Critical", "High")
            and str(q.get("status", "Open")).lower() not in CLOSED_STATUSES]


COMPLETENESS_ITEMS = [
    ("user story", lambda s, d: bool((s.get("user_story") or "").strip())),
    ("description", lambda s, d: bool((s.get("description") or "").strip())),
    ("acceptance criteria", lambda s, d: bool(s.get("acceptance_criteria"))),
    ("source requirement", lambda s, d: bool(s.get("source_requirement_ids"))),
    ("in-scope list", lambda s, d: bool(s.get("in_scope"))),
    ("technical context", lambda s, d: _has_tech(s)),
    ("tests", lambda s, d: _has_tests(s)),
    ("no open Critical/High questions", lambda s, d: not _blocking_questions(s, d)),
]


def story_completeness(story, data):
    """Percentage of COMPLETENESS_ITEMS the story satisfies, plus the list of missing items."""
    missing = [name for name, ok in COMPLETENESS_ITEMS if not ok(story, data)]
    return _pct(len(COMPLETENESS_ITEMS) - len(missing), len(COMPLETENESS_ITEMS)), missing


def covered_requirement_ids(data):
    return {rid for s in data.get("stories", []) or [] for rid in s.get("source_requirement_ids") or []}


def compute_readiness(data):
    stories = data.get("stories", []) or []
    reqs = _reqs(data)
    project = data.get("project") or {}
    business_parts = [project.get("business_objectives"), project.get("business_actors"),
                      project.get("business_flow"), data.get("business_requirements")]
    covered = covered_requirement_ids(data)
    completeness = [story_completeness(s, data)[0] for s in stories]
    return {
        "business_pct": _pct(sum(1 for p in business_parts if p), len(business_parts)),
        "requirements_pct": _pct(sum(1 for r in reqs if r.get("confidence") == "confirmed"), len(reqs)),
        "technical_context_pct": _pct(sum(1 for s in stories if _has_tech(s)), len(stories)),
        "testing_pct": _pct(sum(1 for s in stories if _has_tests(s)), len(stories)),
        "traceability_pct": _pct(sum(1 for r in reqs if r.get("id") in covered), len(reqs)),
        "story_completeness_avg_pct": round(sum(completeness) / len(completeness)) if completeness else 0,
    }


def apply_computed(data):
    """Return a copy of data with readiness, per-story completeness_pct and traceability
    'covered' flags recomputed from the data itself."""
    out = copy.deepcopy(data)
    for s in out.get("stories", []) or []:
        s["completeness_pct"], s["completeness_missing"] = story_completeness(s, out)
    covered = covered_requirement_ids(out)
    for t in out.get("traceability", []) or []:
        t["covered"] = t.get("requirement_id") in covered
    out["readiness"] = compute_readiness(out)
    return out


# ---------------------------------------------------------------- checks
def _find_cycle(edges):
    """edges: dict node -> set(nodes it depends on). Returns one cycle as a list, or None."""
    WHITE, GREY, BLACK = 0, 1, 2
    color, stack = {}, []

    def visit(n):
        color[n] = GREY
        stack.append(n)
        for m in sorted(edges.get(n, ())):
            if color.get(m, WHITE) == GREY:
                return stack[stack.index(m):] + [m]
            if color.get(m, WHITE) == WHITE:
                found = visit(m)
                if found:
                    return found
        stack.pop()
        color[n] = BLACK
        return None

    for n in sorted(edges):
        if color.get(n, WHITE) == WHITE:
            found = visit(n)
            if found:
                return found
    return None


def collect_checks(data, schema=None):
    """Returns a list of {label, level, ok, problems}."""
    checks = []

    def check(label, problems, level="FAIL"):
        checks.append({"label": label, "level": level, "ok": not problems, "problems": list(problems)})

    stories = data.get("stories", []) or []
    questions = data.get("open_questions", []) or []
    reqs = _reqs(data)
    story_ids = {s.get("id") for s in stories}
    req_ids = {r.get("id") for r in reqs}
    q_ids = {q.get("id") for q in questions}
    rule_ids = {r.get("id") for r in data.get("business_rules", []) or []}
    story_by_id = {s.get("id"): s for s in stories}

    # --- original checks (kept, same order) ---
    traced_ids = {t.get("requirement_id") for t in data.get("traceability", []) or []}
    check("Every requirement mapped in traceability", sorted(req_ids - traced_ids))
    check("Every story has acceptance criteria",
          [s.get("id") for s in stories if not s.get("acceptance_criteria")])
    gaps = []
    for q in questions:
        for sid in q.get("story_ids") or []:
            st = story_by_id.get(sid)
            if st is None:
                gaps.append(f"{q.get('id')} references missing story {sid}")
            elif q.get("id") not in (st.get("open_question_ids") or []):
                gaps.append(f"{q.get('id')} -> {sid} not reciprocated in story.open_question_ids")
    for s in stories:
        for qid in s.get("open_question_ids") or []:
            q = next((x for x in questions if x.get("id") == qid), None)
            if q is not None and s.get("id") not in (q.get("story_ids") or []):
                gaps.append(f"{s.get('id')} -> {qid} not reciprocated in question.story_ids")
    check("Open-question <-> story cross-links are reciprocal", gaps)
    check("Every open question has severity", [q.get("id") for q in questions if not q.get("severity")])
    check("Every open question has an owner field (may be 'Unassigned')",
          [q.get("id") for q in questions if "owner" not in q])
    check("Every story has a source requirement link",
          [s.get("id") for s in stories if not s.get("source_requirement_ids")])
    check("Every requirement has a confidence marking", [r.get("id") for r in reqs if not r.get("confidence")])
    check("No story has fully blank technical_context", [s.get("id") for s in stories if not _has_tech(s)])
    arch = data.get("architecture") or {}
    names = set(arch.get("flow") or []) | {c.get("name") for c in arch.get("components") or []}
    check("No orphan architecture integration_point edges",
          [f"{p.get('from')} -> {p.get('to')}" for p in arch.get("integration_points") or []
           if p.get("from") not in names or p.get("to") not in names])

    # --- structural checks ---
    if schema is not None:
        check("Data matches decomposition.schema.json", validate_schema(data, schema))
    else:
        check("Data matches decomposition.schema.json",
              ["decomposition.schema.json not found next to quality_gate.py — schema not checked"], "WARN")

    seen, dupes = {}, []
    collections = list(REQ_KEYS) + ["business_rules", "stories", "open_questions", "assumptions", "decisions", "risks"]
    for key in collections:
        for item in data.get(key, []) or []:
            iid = item.get("id")
            if iid in seen:
                dupes.append(f"{iid} (in {seen[iid]} and {key})" if seen[iid] != key else f"{iid} (twice in {key})")
            seen[iid] = key
    check("All IDs are unique", dupes)

    dangling = []

    def refs(owner, ids, valid, kind):
        for i in ids or []:
            if i not in valid:
                dangling.append(f"{owner} -> unknown {kind} {i}")

    for s in stories:
        sid = s.get("id")
        refs(sid, s.get("source_requirement_ids"), req_ids, "requirement")
        refs(sid, s.get("open_question_ids"), q_ids, "question")
        refs(sid, s.get("business_rule_ids"), rule_ids, "business rule")
        refs(sid, [d.get("story_id") for d in s.get("dependencies") or []], story_ids, "story")
    for key in ("business_rules", "assumptions", "decisions", "risks"):
        for item in data.get(key, []) or []:
            refs(item.get("id"), item.get("story_ids"), story_ids, "story")
    for t in data.get("traceability", []) or []:
        refs(f"traceability[{t.get('requirement_id')}]", [t.get("requirement_id")], req_ids, "requirement")
        refs(f"traceability[{t.get('requirement_id')}]", t.get("story_ids"), story_ids, "story")
    for d in data.get("dependencies", []) or []:
        refs("dependencies", [d.get("from"), d.get("to")], story_ids, "story")
    check("Every cross-reference resolves to an existing item", dangling)

    covered = covered_requirement_ids(data)
    trace_problems = []
    for t in data.get("traceability", []) or []:
        rid = t.get("requirement_id")
        citing = sorted(s.get("id") for s in stories if rid in (s.get("source_requirement_ids") or []))
        if t.get("covered") and rid not in covered:
            trace_problems.append(f"{rid} marked covered but no story lists it in source_requirement_ids")
        elif sorted(t.get("story_ids") or []) != citing:
            trace_problems.append(f"{rid}: traceability says {sorted(t.get('story_ids') or [])}, stories say {citing}")
    check("Traceability matrix agrees with the stories", trace_problems)

    depends = {}
    self_deps = []
    for s in stories:
        for d in s.get("dependencies") or []:
            other, rel = d.get("story_id"), d.get("relationship")
            if other == s.get("id"):
                self_deps.append(f"{other} depends on itself")
            elif rel == "depends_on":
                depends.setdefault(s.get("id"), set()).add(other)
            elif rel == "blocks":
                depends.setdefault(other, set()).add(s.get("id"))
    for d in data.get("dependencies", []) or []:
        if d.get("from") == d.get("to"):
            self_deps.append(f"{d.get('from')} depends on itself")
        else:
            depends.setdefault(d.get("from"), set()).add(d.get("to"))
    cycle = _find_cycle(depends)
    check("No circular story dependencies", self_deps + ([" -> ".join(cycle)] if cycle else []))

    screens = {((s.get("technical_context") or {}).get("ui_spec") or {}).get("screen") for s in stories}
    check("Customer-journey UI screens match a story's ui_spec.screen",
          [f"step {f.get('step')}: '{f.get('ui_screen')}'" for f in (data.get("project") or {}).get("business_flow") or []
           if f.get("ui_screen") and f.get("ui_screen") not in screens], "WARN")

    stated = data.get("readiness") or {}
    computed = compute_readiness(data)
    drift = [f"{k}: estimated {stated[k]}%, data shows {v}%" for k, v in computed.items()
             if isinstance(stated.get(k), (int, float)) and abs(stated[k] - v) > 20]
    check("Estimated readiness is consistent with the data (portal uses computed values)", drift, "WARN")

    return checks


def load_schema():
    if not os.path.exists(SCHEMA_PATH):
        return None
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def run(data_path, as_json=False):
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    checks = collect_checks(data, load_schema())
    failed = [c for c in checks if not c["ok"] and c["level"] == "FAIL"]

    if as_json:
        print(json.dumps({
            "passed": not failed,
            "failures": len(failed),
            "warnings": sum(1 for c in checks if not c["ok"] and c["level"] == "WARN"),
            "checks": checks,
            "computed_readiness": compute_readiness(data),
        }, indent=2))
    else:
        for i, c in enumerate(checks, 1):
            status = "PASS" if c["ok"] else c["level"]
            print(f"[{status}] {i}. {c['label']}")
            for p in c["problems"][:MAX_SHOWN]:
                print(f"         - {p}")
            if len(c["problems"]) > MAX_SHOWN:
                print(f"         ... and {len(c['problems']) - MAX_SHOWN} more")
        print()
        if failed:
            print(f"GATE FAILED — {len(failed)} check(s) did not pass. Fix before generating the portal.")
        else:
            print("GATE PASSED — all checks clean." if all(c["ok"] for c in checks)
                  else "GATE PASSED — with warnings (see above).")
    return 1 if failed else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--json"]
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)
    sys.exit(run(args[0], as_json="--json" in sys.argv[1:]))
