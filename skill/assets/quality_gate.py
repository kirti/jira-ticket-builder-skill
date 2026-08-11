#!/usr/bin/env python3
"""
Runs the D5 quality gate against a decomposition JSON file and reports pass/fail
per check. Run this before generating the portal — don't re-derive these checks
ad hoc each time; that has produced the same class of bug (an open question's
story_ids pointing at a story that doesn't list the question back in its own
open_question_ids) on every decomposition run tested so far.

Usage:
    python3 quality_gate.py <data_json_path>

Exits non-zero if any check fails, so it can be used as a hard gate in a script,
not just an informational printout.
"""
import json
import sys


def run(data_path):
    with open(data_path) as f:
        data = json.load(f)

    failures = []

    def check(label, condition_ok, detail=""):
        status = "PASS" if condition_ok else "FAIL"
        print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition_ok else ""))
        if not condition_ok:
            failures.append(label)

    all_req_ids = {r['id'] for r in data.get('business_requirements', [])
                   + data.get('functional_requirements', [])
                   + data.get('non_functional_requirements', [])}
    traced_ids = {t['requirement_id'] for t in data.get('traceability', [])}
    missing_trace = all_req_ids - traced_ids
    check("1. Every requirement mapped in traceability", not missing_trace, str(missing_trace))

    no_ac = [s['id'] for s in data.get('stories', []) if not s.get('acceptance_criteria')]
    check("2. Every story has acceptance criteria", not no_ac, str(no_ac))

    # This is the check that has caught a real bug on every decomposition tested
    # so far: a question's own story_ids says it affects a story, but that story's
    # open_question_ids doesn't list the question back. Cross-link, not one-way.
    cross_link_gaps = []
    story_by_id = {s['id']: s for s in data.get('stories', [])}
    for q in data.get('open_questions', []):
        for sid in q.get('story_ids', []):
            story = story_by_id.get(sid)
            if story is None:
                cross_link_gaps.append(f"{q['id']} references missing story {sid}")
            elif q['id'] not in story.get('open_question_ids', []):
                cross_link_gaps.append(f"{q['id']} -> {sid} not reciprocated in story.open_question_ids")
    check("3. Open-question <-> story cross-links are reciprocal", not cross_link_gaps, str(cross_link_gaps))

    no_sev = [q['id'] for q in data.get('open_questions', []) if not q.get('severity')]
    no_owner = [q['id'] for q in data.get('open_questions', []) if 'owner' not in q]
    check("4. Every open question has severity", not no_sev, str(no_sev))
    check("5. Every open question has an owner field (may be 'Unassigned')", not no_owner, str(no_owner))

    no_source = [s['id'] for s in data.get('stories', []) if not s.get('source_requirement_ids')]
    check("6. Every story has a source requirement link", not no_source, str(no_source))

    all_reqs = (data.get('business_requirements', []) + data.get('functional_requirements', [])
                + data.get('non_functional_requirements', []))
    no_conf = [r['id'] for r in all_reqs if not r.get('confidence')]
    check("7. Every requirement has a confidence marking", not no_conf, str(no_conf))

    blank_tc = [s['id'] for s in data.get('stories', [])
                if not s.get('technical_context', {}).get('affected_systems')
                and not s.get('technical_context', {}).get('apis')]
    check("8. No story has fully blank technical_context", not blank_tc, str(blank_tc))

    arch = data.get('architecture', {})
    names = set(arch.get('flow', [])) | {c['name'] for c in arch.get('components', [])}
    orphans = [(p['from'], p['to']) for p in arch.get('integration_points', [])
               if p['from'] not in names or p['to'] not in names]
    check("9. No orphan architecture integration_point edges", not orphans, str(orphans))

    print()
    if failures:
        print(f"GATE FAILED — {len(failures)} check(s) did not pass. Fix before generating the portal.")
        return 1
    else:
        print("GATE PASSED — all checks clean.")
        return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(run(sys.argv[1]))
