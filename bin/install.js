#!/usr/bin/env node
/**
 * Installs the jira-ticket-builder skill files into the current project.
 *
 * Usage:
 *   npx jira-ticket-builder-skill                        # Claude skill -> .claude/skills/jira-ticket-builder-skill
 *   npx jira-ticket-builder-skill --target <dir>         # install the skill somewhere else
 *   npx jira-ticket-builder-skill --prompt               # also install the portable prompt for ChatGPT/other LLMs
 *   npx jira-ticket-builder-skill --prompt-target <dir>  # choose where the portable prompt goes
 *   npx jira-ticket-builder-skill --force                # replace an existing install (removes stale files)
 *   npx jira-ticket-builder-skill --dry-run              # show what would be installed, write nothing
 */
'use strict';
const fs = require('fs');
const path = require('path');

const pkg = require('../package.json');
const packageRoot = path.join(__dirname, '..');
const SKILL_SRC = path.join(packageRoot, 'skill');
const PROMPT_SRC = path.join(packageRoot, 'prompt');
const SKIP = new Set(['__pycache__', '.DS_Store']);

const HELP = `jira-ticket-builder-skill v${pkg.version}

Usage: npx jira-ticket-builder-skill [options]

Options:
  --target <dir>         Skill install dir (default: ./.claude/skills/jira-ticket-builder-skill)
  --prompt               Also install the portable prompt (ChatGPT / other LLMs)
  --prompt-target <dir>  Prompt install dir (default: ./jira-ticket-builder-prompt)
  --force                Overwrite an existing install, removing stale files
  --dry-run              List what would be installed without writing anything
  -v, --version          Print version
  -h, --help             Show this help`;

function parseArgs(argv) {
  const opts = { prompt: false, force: false, dryRun: false, target: null, promptTarget: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const needValue = () => {
      const v = argv[++i];
      if (!v || v.startsWith('--')) throw new Error(`${a} requires a directory argument`);
      return v;
    };
    switch (a) {
      case '--target': opts.target = needValue(); break;
      case '--prompt-target': opts.promptTarget = needValue(); opts.prompt = true; break;
      case '--prompt': opts.prompt = true; break;
      case '--force': opts.force = true; break;
      case '--dry-run': opts.dryRun = true; break;
      case '-v': case '--version': opts.version = true; break;
      case '-h': case '--help': opts.help = true; break;
      default: throw new Error(`Unknown option: ${a}`);
    }
  }
  return opts;
}

function listFiles(src, rel = '') {
  const out = [];
  for (const entry of fs.readdirSync(path.join(src, rel), { withFileTypes: true })) {
    if (SKIP.has(entry.name)) continue;
    const r = path.join(rel, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(src, r));
    else out.push(r);
  }
  return out;
}

function install(label, src, dest, { force, dryRun }) {
  const files = listFiles(src);
  if (fs.existsSync(dest) && fs.readdirSync(dest).length > 0) {
    if (!force) {
      throw new Error(`${dest} already exists. Re-run with --force to replace it.`);
    }
    console.log(`${dryRun ? '[dry-run] Would replace' : 'Replacing'} existing ${label} at: ${dest}`);
    if (!dryRun) fs.rmSync(dest, { recursive: true, force: true });
  } else {
    console.log(`${dryRun ? '[dry-run] Would install' : 'Installing'} ${label} to: ${dest}`);
  }
  for (const f of files) {
    if (dryRun) { console.log(`  ${f}`); continue; }
    const d = path.join(dest, f);
    fs.mkdirSync(path.dirname(d), { recursive: true });
    fs.copyFileSync(path.join(src, f), d);
  }
  console.log(`  ${files.length} files`);
}

function main(argv) {
  let opts;
  try { opts = parseArgs(argv); } catch (e) {
    console.error(`Error: ${e.message}\n\n${HELP}`);
    return 2;
  }
  if (opts.help) { console.log(HELP); return 0; }
  if (opts.version) { console.log(pkg.version); return 0; }

  const cwd = process.cwd();
  const skillTarget = path.resolve(cwd, opts.target || path.join('.claude', 'skills', 'jira-ticket-builder-skill'));
  // Kept OUTSIDE .claude/skills/ on purpose: anything in that folder is scanned as a skill,
  // and the prompt folder has no SKILL.md.
  const promptTarget = path.resolve(cwd, opts.promptTarget || 'jira-ticket-builder-prompt');

  try {
    install('Claude skill', SKILL_SRC, skillTarget, opts);
    if (opts.prompt) install('portable prompt', PROMPT_SRC, promptTarget, opts);
  } catch (e) {
    console.error(`Error: ${e.message}`);
    return 1;
  }

  if (!opts.dryRun) {
    console.log('\nDone.');
    console.log('- Claude Code / Cowork: the skill is picked up automatically from .claude/skills/');
    console.log(opts.prompt
      ? `- ChatGPT or other LLMs: use ${path.relative(cwd, promptTarget) || '.'}/INSTRUCTIONS.md as the system prompt`
      : '- ChatGPT or other LLMs: re-run with --prompt to install INSTRUCTIONS.md');
  }
  return 0;
}

if (require.main === module) process.exitCode = main(process.argv.slice(2));
module.exports = { main, parseArgs };
