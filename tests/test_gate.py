import copy, io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skill", "assets"))
import quality_gate  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def fixture(name="multi.json"):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def failing(data):
    """Labels of FAIL-level checks that did not pass."""
    return [c["label"] for c in quality_gate.collect_checks(data, quality_gate.load_schema())
            if not c["ok"] and c["level"] == "FAIL"]


def problems(data, label_part):
    for c in quality_gate.collect_checks(data, quality_gate.load_schema()):
        if label_part in c["label"]:
            return c["problems"]
    raise AssertionError(f"no check matching {label_part!r}")


class GateTests(unittest.TestCase):
    def test_fixtures_pass(self):
        for name in ("valid.json", "multi.json"):
            self.assertEqual(failing(fixture(name)), [], name)

    def test_non_reciprocal_cross_link_fails_both_directions(self):
        d = fixture()
        d["stories"][1]["open_question_ids"] = []
        self.assertIn("Open-question <-> story cross-links are reciprocal", failing(d))
        d = fixture()
        d["open_questions"][0]["story_ids"] = []
        self.assertIn("Open-question <-> story cross-links are reciprocal", failing(d))

    def test_orphan_architecture_edge_fails(self):
        d = fixture()
        d["architecture"]["integration_points"].append({"from": "Web", "to": "Ghost"})
        self.assertIn("No orphan architecture integration_point edges", failing(d))

    def test_schema_enum_and_type_errors(self):
        d = fixture()
        d["open_questions"][0]["severity"] = "urgent"
        d["stories"][0]["acceptance_criteria"] = "just do it"
        found = problems(d, "schema")
        self.assertTrue(any("severity" in p and "urgent" in p for p in found), found)
        self.assertTrue(any("acceptance_criteria: expected array" in p for p in found), found)

    def test_duplicate_ids_fail(self):
        d = fixture()
        d["stories"].append(copy.deepcopy(d["stories"][0]))
        self.assertTrue(any("STORY-001" in p for p in problems(d, "unique")))

    def test_dangling_references_fail(self):
        d = fixture()
        d["stories"][0]["source_requirement_ids"].append("FR-999")
        d["stories"][1]["dependencies"][0]["story_id"] = "STORY-404"
        found = problems(d, "cross-reference")
        self.assertIn("STORY-001 -> unknown requirement FR-999", found)
        self.assertIn("STORY-002 -> unknown story STORY-404", found)

    def test_traceability_must_agree_with_stories(self):
        d = fixture()
        d["traceability"][1]["story_ids"] = ["STORY-002"]
        self.assertTrue(any(p.startswith("FR-001") for p in problems(d, "Traceability matrix")))
        d = fixture()
        d["stories"][2]["source_requirement_ids"] = ["FR-001"]
        self.assertTrue(any("FR-003 marked covered" in p for p in problems(d, "Traceability matrix")))

    def test_dependency_cycle_fails(self):
        d = fixture()
        d["stories"][0]["dependencies"] = [{"story_id": "STORY-002", "relationship": "depends_on"}]
        found = problems(d, "circular")
        self.assertEqual(len(found), 1)
        self.assertIn("STORY-001", found[0])
        self.assertIn("STORY-002", found[0])

    def test_blocks_relationship_participates_in_cycles(self):
        d = fixture()
        d["stories"][1]["dependencies"].append({"story_id": "STORY-001", "relationship": "blocks"})
        self.assertTrue(problems(d, "circular"))

    def test_warnings_do_not_fail_gate(self):
        d = fixture()
        d["project"]["business_flow"][0]["ui_screen"] = "Nowhere"
        d["readiness"]["testing_pct"] = 10
        self.assertEqual(failing(d), [])
        self.assertTrue(problems(d, "UI screens"))
        self.assertTrue(problems(d, "readiness"))

    def test_json_output(self):
        d = fixture()
        d["stories"][0]["acceptance_criteria"] = []
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(d, f)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = quality_gate.run(f.name, as_json=True)
        finally:
            os.unlink(f.name)
        report = json.loads(buf.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])
        self.assertIn("computed_readiness", report)


class MetricsTests(unittest.TestCase):
    def test_compute_readiness(self):
        r = quality_gate.compute_readiness(fixture())
        self.assertEqual(r["requirements_pct"], 60)      # 3 of 5 confirmed
        self.assertEqual(r["traceability_pct"], 100)
        self.assertEqual(r["story_completeness_avg_pct"], 96)  # STORY-002 has an open Critical question

    def test_story_completeness_lists_missing_items(self):
        d = fixture()
        pct, missing = quality_gate.story_completeness(d["stories"][1], d)
        self.assertEqual(pct, 88)
        self.assertEqual(missing, ["no open Critical/High questions"])
        d["open_questions"][0]["status"] = "Resolved"
        self.assertEqual(quality_gate.story_completeness(d["stories"][1], d)[0], 100)

    def test_empty_data_does_not_crash(self):
        r = quality_gate.compute_readiness({})
        self.assertTrue(all(v == 0 for v in r.values()))
        quality_gate.collect_checks({}, quality_gate.load_schema())


if __name__ == "__main__":
    unittest.main()
