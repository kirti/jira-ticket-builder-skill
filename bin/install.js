#!/usr/bin/env node
/**
 * Installs the jira-ticket-builder skill files into the current project.
 *
 * Usage:
 *   npx jira-ticket-builder-skill                 # installs the Claude skill into .claude/skills/
 *   npx jira-ticket-builder-skill --target <dir>  # installs into a custom directory
 *   npx jira-ticket-builder-skill --prompt        # also copies the portable prompt/ folder
 */
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const targetFlagIdx = args.indexOf('--target');
const includePrompt = args.includes('--prompt');

const defaultTarget = path.join(process.cwd(), '.claude', 'skills', 'jira-ticket-builder-skill');
const target = targetFlagIdx !== -1 && args[targetFlagIdx + 1]
  ? path.resolve(args[targetFlagIdx + 1])
  : defaultTarget;

const packageRoot = path.join(__dirname, '..');
const skillSrc = path.join(packageRoot, 'skill');
const promptSrc = path.join(packageRoot, 'prompt');

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === '__pycache__') continue;
      copyDir(s, d);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

console.log(`Installing Claude skill to: ${target}`);
copyDir(skillSrc, target);

if (includePrompt) {
  const promptTarget = path.join(path.dirname(target), 'jira-ticket-builder-prompt');
  console.log(`Installing portable prompt to: ${promptTarget}`);
  copyDir(promptSrc, promptTarget);
}

console.log('\nDone.');
console.log('- Claude / Claude Code: the skill will be picked up automatically from .claude/skills/');
console.log('- ChatGPT or other LLMs: see prompt/INSTRUCTIONS.md (run with --prompt to install it)');
