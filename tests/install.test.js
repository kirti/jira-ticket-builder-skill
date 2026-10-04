'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const BIN = path.join(__dirname, '..', 'bin', 'install.js');
const pkg = require('../package.json');

function run(args, cwd) {
  return spawnSync(process.execPath, [BIN, ...args], { cwd, encoding: 'utf8' });
}
function tmp() { return fs.mkdtempSync(path.join(os.tmpdir(), 'jtb-install-')); }
const SKILL = path.join('.claude', 'skills', 'jira-ticket-builder-skill');

test('default install puts the skill in .claude/skills', () => {
  const cwd = tmp();
  const r = run([], cwd);
  assert.strictEqual(r.status, 0, r.stderr);
  for (const f of ['SKILL.md', 'assets/build_portal.py', 'assets/quality_gate.py', 'references/decomposition-schema.md']) {
    assert.ok(fs.existsSync(path.join(cwd, SKILL, f)), f);
  }
  assert.ok(!fs.existsSync(path.join(cwd, 'jira-ticket-builder-prompt')));
});

test('--prompt installs outside .claude/skills', () => {
  const cwd = tmp();
  assert.strictEqual(run(['--prompt'], cwd).status, 0);
  assert.ok(fs.existsSync(path.join(cwd, 'jira-ticket-builder-prompt', 'INSTRUCTIONS.md')));
  const skillsDir = fs.readdirSync(path.join(cwd, '.claude', 'skills'));
  assert.deepStrictEqual(skillsDir, ['jira-ticket-builder-skill']);
});

test('refuses to overwrite without --force, and --force removes stale files', () => {
  const cwd = tmp();
  assert.strictEqual(run([], cwd).status, 0);
  const stale = path.join(cwd, SKILL, 'stale.txt');
  fs.writeFileSync(stale, 'old');
  const again = run([], cwd);
  assert.strictEqual(again.status, 1);
  assert.match(again.stderr, /--force/);
  assert.strictEqual(run(['--force'], cwd).status, 0);
  assert.ok(!fs.existsSync(stale));
});

test('--dry-run writes nothing', () => {
  const cwd = tmp();
  const r = run(['--dry-run', '--prompt'], cwd);
  assert.strictEqual(r.status, 0);
  assert.match(r.stdout, /SKILL\.md/);
  assert.deepStrictEqual(fs.readdirSync(cwd), []);
});

test('--target and --prompt-target are honoured', () => {
  const cwd = tmp();
  assert.strictEqual(run(['--target', 'a/skill', '--prompt-target', 'b/prompt'], cwd).status, 0);
  assert.ok(fs.existsSync(path.join(cwd, 'a', 'skill', 'SKILL.md')));
  assert.ok(fs.existsSync(path.join(cwd, 'b', 'prompt', 'INSTRUCTIONS.md')));
});

test('--version, --help, and bad flags', () => {
  const cwd = tmp();
  assert.strictEqual(run(['--version'], cwd).stdout.trim(), pkg.version);
  assert.match(run(['--help'], cwd).stdout, /Usage:/);
  const bad = run(['--nope'], cwd);
  assert.strictEqual(bad.status, 2);
  assert.match(bad.stderr, /Unknown option/);
  assert.strictEqual(run(['--target'], cwd).status, 2);
});

test('no __pycache__ is ever copied', () => {
  const cwd = tmp();
  const cache = path.join(__dirname, '..', 'skill', 'assets', '__pycache__');
  fs.mkdirSync(cache, { recursive: true });
  try {
    assert.strictEqual(run([], cwd).status, 0);
    assert.ok(!fs.existsSync(path.join(cwd, SKILL, 'assets', '__pycache__')));
  } finally { fs.rmSync(cache, { recursive: true, force: true }); }
});
