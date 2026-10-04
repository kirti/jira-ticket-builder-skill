import copy, json, os, re, subprocess, sys, tempfile, unittest, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "skill", "assets")
TEMPLATE = os.path.join(ASSETS, "portal-page-template.html")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "valid.json")
sys.path.insert(0, ASSETS)
import build_portal  # noqa: E402
import quality_gate  # noqa: E402


def load_fixture():
    with open(FIXTURE) as f:
        return json.load(f)


class BuildPortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "portal")

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8") as f:
            return f.read()

    def test_writes_all_pages_plus_shared_data(self):
        build_portal.build(TEMPLATE, FIXTURE, self.out)
        files = sorted(os.listdir(self.out))
        self.assertEqual(len(files), 13)
        self.assertIn("portal-data.js", files)
        for name in build_portal.FILENAMES.values():
            self.assertIn(name, files)

    def test_shared_mode_does_not_embed_data(self):
        build_portal.build(TEMPLATE, FIXTURE, self.out)
        page = self.read("index.html")
        self.assertIn('<script src="portal-data.js"></script>', page)
        self.assertNotIn('window.PORTAL_DATA = {"', page, "data should live in portal-data.js")

    def test_current_view_set_per_page(self):
        build_portal.build(TEMPLATE, FIXTURE, self.out)
        self.assertIn('let CURRENT_VIEW = "stories"', self.read("stories.html"))
        self.assertNotIn("__CURRENT_VIEW__", self.read("index.html"))

    def test_closing_script_tag_in_data_is_neutralised(self):
        for inline in (False, True):
            build_portal.build(TEMPLATE, FIXTURE, self.out, inline=inline)
            blob = self.read("index.html") + ("" if inline else self.read("portal-data.js"))
            self.assertNotIn("</script><img", blob)
            self.assertEqual(blob.count("</script>"), self.read("index.html").count("<script"))

    def test_escaped_json_round_trips(self):
        data = load_fixture()
        data["project"]["name"] = "a</script>&<!-- \u2028 \u2029 b"
        s = build_portal.safe_json_for_script(data)
        self.assertNotRegex(s, r"[<>&\u2028\u2029]")
        self.assertEqual(json.loads(s), data)

    def test_inline_mode_removes_stale_data_file(self):
        build_portal.build(TEMPLATE, FIXTURE, self.out)
        build_portal.build(TEMPLATE, FIXTURE, self.out, inline=True)
        self.assertNotIn("portal-data.js", os.listdir(self.out))
        self.assertTrue('window.PORTAL_DATA = {"' in self.read("index.html"), "data not inlined")

    def test_zip_contains_every_page(self):
        zp = os.path.join(self.tmp.name, "portal.zip")
        build_portal.build(TEMPLATE, FIXTURE, self.out, zip_path=zp)
        with zipfile.ZipFile(zp) as z:
            self.assertEqual(sorted(z.namelist()), sorted(os.listdir(self.out)))

    def test_check_flag_blocks_bad_data(self):
        bad = load_fixture()
        bad["stories"][0]["acceptance_criteria"] = []
        bad_path = os.path.join(self.tmp.name, "bad.json")
        with open(bad_path, "w") as f:
            json.dump(bad, f)
        with self.assertRaises(SystemExit):
            build_portal.build(TEMPLATE, bad_path, self.out, check=True)
        self.assertFalse(os.path.exists(self.out))

    def test_metrics_recomputed_by_default(self):
        data = load_fixture()
        data["readiness"]["testing_pct"] = 3
        data["stories"][0]["completeness_pct"] = 7
        data["traceability"][0]["covered"] = False
        path = os.path.join(self.tmp.name, "d.json")
        with open(path, "w") as f:
            json.dump(data, f)
        build_portal.build(TEMPLATE, path, self.out)
        js = self.read("portal-data.js")
        built = json.loads(js[len("window.PORTAL_DATA = "):-2])
        self.assertEqual(built["readiness"]["testing_pct"], 100)
        self.assertEqual(built["stories"][0]["completeness_pct"], 88)  # open High question Q-1
        self.assertEqual(built["stories"][0]["completeness_missing"], ["no open Critical/High questions"])
        self.assertTrue(built["traceability"][0]["covered"])
        build_portal.build(TEMPLATE, path, self.out, model_metrics=True)
        built = json.loads(self.read("portal-data.js")[len("window.PORTAL_DATA = "):-2])
        self.assertEqual(built["readiness"]["testing_pct"], 3)

    def test_single_file_writes_one_page_and_removes_stale_pages(self):
        build_portal.build(TEMPLATE, FIXTURE, self.out)
        build_portal.build(TEMPLATE, FIXTURE, self.out, single_file=True)
        self.assertEqual(os.listdir(self.out), ["index.html"])
        page = self.read("index.html")
        self.assertIn('let CURRENT_VIEW = "__single__"', page)
        self.assertIn('window.PORTAL_DATA = {"', page)

    def test_single_file_rejects_inline(self):
        r = subprocess.run([sys.executable, os.path.join(ASSETS, "build_portal.py"), TEMPLATE, FIXTURE,
                            self.out, "--single-file", "--inline"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_cli_backwards_compatible(self):
        r = subprocess.run([sys.executable, os.path.join(ASSETS, "build_portal.py"),
                            TEMPLATE, FIXTURE, self.out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("12 pages", r.stdout)


class TemplateTests(unittest.TestCase):
    def test_esc_escapes_quotes(self):
        with open(TEMPLATE) as f:
            t = f.read()
        line = next(l for l in t.splitlines() if l.startswith("function esc("))
        self.assertIn("&quot;", line)
        self.assertIn("&#39;", line)


if __name__ == "__main__":
    unittest.main()
