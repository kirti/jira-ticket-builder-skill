import csv, json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "skill", "assets")
sys.path.insert(0, ASSETS)
import export_jira  # noqa: E402

MULTI = os.path.join(ROOT, "tests", "fixtures", "multi.json")


def fixture():
    with open(MULTI) as f:
        return json.load(f)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def export_csv(self, *args, data=None):
        src = MULTI
        if data is not None:
            src = os.path.join(self.tmp.name, "d.json")
            with open(src, "w") as f:
                json.dump(data, f)
        out = os.path.join(self.tmp.name, "out.csv")
        export_jira.main([src, "--csv", out, *args])
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        header, body = rows[0], rows[1:]
        return header, [dict(row=r, get=lambda name, r=r, h=header: [v for k, v in zip(h, r) if k == name and v])
                        for r in body]

    def test_epic_first_and_parent_set(self):
        header, rows = self.export_csv()
        self.assertEqual(rows[0]["get"]("Issue Type"), ["Epic"])
        self.assertEqual(rows[0]["get"]("Summary"), ["Checkout Revamp"])
        for r in rows[1:]:
            self.assertEqual(r["get"]("Parent"), ["1"])
        self.assertEqual(len(rows), 4)

    def test_link_directions(self):
        _, rows = self.export_csv()
        by_summary = {r["get"]("Summary")[0]: r for r in rows}
        ids = {k: v["get"]("Issue Id")[0] for k, v in by_summary.items()}
        # STORY-002 depends_on STORY-001  ==>  "View cart" blocks "Pay by card"
        self.assertEqual(by_summary["View cart"]["get"]('Link "blocks"'), [ids["Pay by card"]])
        self.assertEqual(by_summary["Pay by card"]["get"]('Link "blocks"'), [])
        # relates_to declared on both sides becomes a single link
        relates = sum(len(r["get"]('Link "relates"')) for r in rows)
        self.assertEqual(relates, 1)

    def test_types_labels_and_type_map(self):
        _, rows = self.export_csv()
        spike = next(r for r in rows if r["get"]("Summary") == ["Wallet spike"])
        self.assertEqual(spike["get"]("Issue Type"), ["Task"])
        self.assertIn("spike", spike["get"]("Labels"))
        pay = next(r for r in rows if r["get"]("Summary") == ["Pay by card"])
        self.assertIn("needs-clarification", pay["get"]("Labels"))
        _, rows = self.export_csv("--type-map", "Spike=Spike", "--label", "Q4 Release")
        spike = next(r for r in rows if r["get"]("Summary") == ["Wallet spike"])
        self.assertEqual(spike["get"]("Issue Type"), ["Spike"])
        self.assertIn("q4-release", spike["get"]("Labels"))

    def test_no_epic(self):
        header, rows = self.export_csv("--no-epic")
        self.assertNotIn("Parent", header)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["get"]("Issue Id"), ["1"])

    def test_description_content_and_escaping(self):
        d = fixture()
        d["stories"][0]["description"] = "Use {code} and [link]"
        _, rows = self.export_csv(data=d)
        desc = rows[1]["get"]("Description")[0]
        self.assertIn("h3. Acceptance criteria", desc)
        self.assertIn("*Given* a cart", desc)
        self.assertIn("Use \\{code\\} and \\[link\\]", desc)
        self.assertIn("FR-001: Show cart", desc)
        pay = rows[2]["get"]("Description")[0]
        self.assertIn("Q-001 (Critical): Which PSP?", pay)

    def test_long_description_truncated(self):
        d = fixture()
        d["stories"][0]["description"] = "x" * 40000
        _, rows = self.export_csv(data=d)
        self.assertLessEqual(len(rows[1]["get"]("Description")[0]), export_jira.JIRA_DESCRIPTION_LIMIT)

    def test_markdown(self):
        out = os.path.join(self.tmp.name, "s.md")
        export_jira.main([MULTI, "--md", out])
        with open(out) as f:
            md = f.read()
        for title in ("STORY-001 — View cart", "STORY-002 — Pay by card", "STORY-003 — Wallet spike"):
            self.assertIn(f"## {title}", md)
        self.assertIn("**Given** a cart", md)

    def test_requires_an_output(self):
        r = subprocess.run([sys.executable, os.path.join(ASSETS, "export_jira.py"), MULTI],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
