# Changelog

## 1.2.0

### Added
- **Jira import export** (`export_jira.py`). Turns the decomposition into a CSV for Jira's bulk
  importer — one Epic plus a row per story, descriptions in Jira markup, labels (story type,
  capability, `needs-clarification` when a Critical/High question is open), the epic as Parent,
  and "blocks" / "relates" links derived from story dependencies — plus a Markdown version of the
  same stories. Replaces the hand-written Markdown step in the skill instructions.
- **Single-file portal** (`build_portal.py --single-file`). One self-contained `index.html` with
  all 12 views, switched via the URL hash. Opens on its own, no zip to extract. The skill now
  delivers this by default; multi-page + zip is kept for people who want separate pages.
- **Machine-readable schema** (`decomposition.schema.json`), validated by the quality gate with
  a small built-in validator (still no Python dependencies).
- **New quality-gate checks:** schema validity, unique IDs, every cross-reference resolves,
  traceability matrix agrees with stories, reciprocal question links in both directions, no
  circular or self dependencies; plus WARN-level checks for unmatched customer-journey screens
  and estimated readiness that's far from the data. `--json` gives a machine-readable report.
- **Computed metrics.** Readiness percentages, per-story completeness (with the list of what's
  missing, shown in the story drawer) and traceability coverage are calculated from the data.
  `--model-metrics` keeps the model's own numbers.

### Changed
- The quality gate is stricter: data that passed 1.1 can fail on dangling references, duplicate
  IDs, schema violations (e.g. lowercase severities) or a traceability matrix that disagrees with
  the stories. Each failure lists exactly what to fix.
- `build_portal.py --check` and computed metrics need `quality_gate.py` and
  `decomposition.schema.json` next to `build_portal.py`; the skill instructions now say to copy the
  whole `assets/` folder.

## 1.1.0

### Security
- **Fixed script injection in generated portals.** `build_portal.py` embedded the data with plain
  `json.dumps`, so any value containing `</script>` (e.g. pasted from a requirements doc) closed
  the script tag early — breaking the page or executing injected markup. Data is now serialised
  with `<`, `>`, `&`, U+2028 and U+2029 escaped.
- The portal's `esc()` helper now escapes `"` and `'`, so values used in HTML attributes can't
  break out of them. Values that previously bypassed `esc()` (ID lists, severities, statuses,
  flow step numbers, percentages) are now escaped or coerced to numbers.

### Performance
- The portal dataset is written once to `portal-data.js` instead of being copied into all 12 pages,
  so a 1,000-story portal drops from 14 MB to 1.7 MB (100 stories: 1.9 MB → 0.7 MB). Use `--inline`
  for the old behaviour.
- The npm tarball no longer ships the README screenshots (670 KB → 45 KB). The README
  references them by absolute URL, so they still display on npm and GitHub.

### Added
- `build_portal.py --check` runs the quality gate and refuses to build on failure.
- `build_portal.py --zip PATH` packages the portal for delivery.
- Installer: `--help`, `--version`, `--force`, `--dry-run`, `--prompt-target`, clear errors and
  exit codes for unknown flags, and a refusal to silently overwrite an existing install.
- Test suite (`npm test`): Python unit tests for the build script and quality gate, installer
  tests, and jsdom tests that render all 12 pages with hostile data. Runs on `prepublishOnly`
  and in GitHub Actions.

### Changed
- `--prompt` now installs to `./jira-ticket-builder-prompt` instead of inside `.claude/skills/`,
  where Claude would scan it as a (broken) skill.
- `--force` removes stale files from older installs instead of copying over them.
- Minimum Node version is now 14.14 (for `fs.rmSync`).

### Fixed
- `build_portal.py` docstring listed 10 pages; it generates 12.
- README: removed the outdated "not yet published" setup instructions; documented installer
  and build options.
- `package.json`: filled in `author`.

## 1.0.0
- Initial release.
