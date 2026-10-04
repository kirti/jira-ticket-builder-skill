'use strict';
// Renders every generated portal page in jsdom and checks it works end to end:
// data loads from portal-data.js, the page renders, nav links resolve, and
// hostile strings in the data stay text instead of becoming markup.
const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');

const ROOT = path.join(__dirname, '..');
const ASSETS = path.join(ROOT, 'skill', 'assets');
const HOSTILE = '"\'><img src=x onerror="window.__pwned=1"></script><script>window.__pwned=1</script>';

class FileOnlyLoader extends ResourceLoader {
  fetch(url, opts) { return url.startsWith('file:') ? super.fetch(url, opts) : null; }
}

function buildPortal(data, extraArgs = []) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'portal-'));
  const dataPath = path.join(dir, 'data.json');
  fs.writeFileSync(dataPath, JSON.stringify(data));
  const out = path.join(dir, 'out');
  execFileSync('python3', [path.join(ASSETS, 'build_portal.py'),
    path.join(ASSETS, 'portal-page-template.html'), dataPath, out, ...extraArgs]);
  return out;
}

async function render(file) {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', (e) => { if (!/^Not implemented/.test(e.message)) errors.push(e.message); });
  const dom = await JSDOM.fromFile(file, {
    runScripts: 'dangerously', resources: new FileOnlyLoader(), virtualConsole,
  });
  await new Promise((r) => dom.window.addEventListener('load', r));
  return { dom, errors };
}

function hostileFixture() {
  const d = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'valid.json'), 'utf8'));
  d.project.name = HOSTILE;
  d.project.business_actors[0].description = HOSTILE;
  d.functional_requirements[0].text = HOSTILE;
  d.stories[0].title = HOSTILE;
  d.stories[0].source_requirement_ids.push(HOSTILE);
  d.open_questions[0].severity = HOSTILE;
  return d;
}

for (const mode of ['shared', 'inline']) {
  test(`all 12 pages render without errors (${mode} data)`, async () => {
    const out = buildPortal(hostileFixture(), mode === 'inline' ? ['--inline'] : []);
    const pages = fs.readdirSync(out).filter((f) => f.endsWith('.html'));
    assert.strictEqual(pages.length, 12);
    for (const page of pages) {
      const { dom, errors } = await render(path.join(out, page));
      const { document } = dom.window;
      assert.deepStrictEqual(errors, [], `${page}: script errors`);
      assert.ok(dom.window.PORTAL_DATA, `${page}: data not loaded`);
      assert.ok(document.getElementById('main').children.length > 0, `${page}: nothing rendered`);
      assert.strictEqual(document.querySelectorAll('#main img, #rail img').length, 0, `${page}: injected markup`);
      assert.strictEqual(dom.window.__pwned, undefined, `${page}: injected script ran`);
      for (const a of document.querySelectorAll('nav.rail a')) {
        assert.ok(fs.existsSync(path.join(out, a.getAttribute('href'))), `${page}: dead link ${a.href}`);
      }
      dom.window.close();
    }
  });
}

test('single-file portal: every view reachable by hash, nothing injected', async () => {
  const out = buildPortal(hostileFixture(), ['--single-file']);
  assert.deepStrictEqual(fs.readdirSync(out), ['index.html']);
  const { dom, errors } = await render(path.join(out, 'index.html'));
  const { window } = dom;
  const { document } = window;
  const links = [...document.querySelectorAll('nav.rail a')].map((a) => a.getAttribute('href'));
  assert.strictEqual(links.length, 12);
  assert.ok(links.every((h) => h.startsWith('#')), 'nav should use hash links');
  for (const href of links) {
    window.location.hash = href;
    window.dispatchEvent(new window.HashChangeEvent('hashchange'));
    const active = document.querySelector('nav.rail a.active');
    assert.strictEqual(active.getAttribute('href'), href, `${href} not active`);
    assert.ok(document.getElementById('main').children.length > 0, `${href}: nothing rendered`);
    assert.strictEqual(document.querySelectorAll('#main img').length, 0, `${href}: injected markup`);
  }
  window.location.hash = '#not-a-view';
  window.dispatchEvent(new window.HashChangeEvent('hashchange'));
  assert.strictEqual(document.querySelector('nav.rail a.active').getAttribute('href'), '#overview');
  assert.deepStrictEqual(errors, []);
  assert.strictEqual(window.__pwned, undefined);
  window.close();
});

test('story drawer shows computed completeness gaps', async () => {
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'multi.json'), 'utf8'));
  const out = buildPortal(data, ['--single-file']);
  const { dom } = await render(path.join(out, 'index.html'));
  const { window } = dom;
  window.location.hash = '#stories';
  window.dispatchEvent(new window.HashChangeEvent('hashchange'));
  const card = [...window.document.querySelectorAll('.story-card')].find((c) => c.textContent.includes('Pay by card'));
  card.onclick();
  const drawer = window.document.getElementById('drawer').textContent;
  assert.match(drawer, /88% complete/);
  assert.match(drawer, /Missing: no open Critical\/High questions/);
  window.close();
});

test('hostile text is displayed literally', async () => {
  const out = buildPortal(hostileFixture());
  const { dom } = await render(path.join(out, 'requirements.html'));
  assert.ok(dom.window.document.getElementById('main').textContent.includes(HOSTILE));
  dom.window.close();
});
