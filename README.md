# jira-ticket-builder-skill

Turns rough input into structured Jira work — either a single ticket, or a full requirements
document decomposed into linked stories with an explorable HTML portal (business flow,
architecture, UI flow, and customer-journey diagrams, all generated from data).

Works as a **Claude Skill** (triggers automatically in Claude.ai, Claude Code, or Cowork) and as
**portable instructions** for any other LLM tool with code execution (ChatGPT Custom GPTs,
ChatGPT Advanced Data Analysis, etc.) — see [Model support](#model-support) below.

## What it does

**Single-ticket mode** — paste a bug report, a one-line feature ask, or meeting notes, and get
back one fully-structured Jira ticket. Supports a quick mode (short, lightweight) and a full
enterprise mode (business context, technical detail, testing strategy, rollout/rollback), adapted
by issue type (Bug, Story, Task, Spike, Tech Debt, Security, Incident).

**Decomposition mode** — hand it a rough requirements document (a product brief, meeting notes, a
spec with open questions scattered through it) and get back:

- Multiple independently-shippable Jira stories, each traced back to its source requirement
- An open-questions map (including gaps the model identifies but you didn't ask, clearly marked)
- A traceability matrix and a delivery-readiness score
- Risks and decisions logs (only populated when something real is there — no filler)
- A 12-page HTML portal: Overview, Business Context (+ flow diagram), Customer Journey (swimlane:
  customer action → UI screen → backend call), Requirements, Stories, Open Questions,
  Traceability, Architecture (+ diagram), UI Flow (+ diagram), Assumptions, Decisions, Risks

## Installation

### Claude Skill

```bash
npx jira-ticket-builder-skill
```

This installs the skill into `.claude/skills/jira-ticket-builder-skill/` in your current
directory. Claude Code and Cowork pick up skills from that location automatically. For Claude.ai,
upload the `skill/` folder's contents (or the packaged `.skill` file, if you have one) via the
skill-creation flow.

### Portable prompt (ChatGPT / other LLMs)

```bash
npx jira-ticket-builder-skill --prompt
```

This additionally installs `jira-ticket-builder-prompt/INSTRUCTIONS.md` alongside the skill
folder. See [Model support](#model-support) for how to use it.

### Manual install

Clone or download this repo; the `skill/` folder is a complete, self-contained Claude Skill
(`SKILL.md` + `assets/` + `references/`).

## Model support

| Environment | How to use it |
|---|---|
| Claude.ai / Claude Code / Cowork | Native skill — triggers automatically once installed |
| ChatGPT (Custom GPT) | Paste `prompt/INSTRUCTIONS.md` into the GPT's Instructions field; upload `skill/assets/` and `skill/references/` as Knowledge files so Code Interpreter can read them |
| Any other LLM with code execution | Use `prompt/INSTRUCTIONS.md` as a system prompt; give the model filesystem access to `skill/assets/` and `skill/references/` |
| A plain chat model with no code execution | Single-ticket mode still works (it's just filling in a markdown template). Decomposition mode's portal-generation step needs to run a Python script, so it requires code execution somewhere in the loop |

The underlying logic — the JSON schema, the markdown templates, and the Python portal-builder
script — is plain data and code with no model-specific API calls, so it behaves identically
regardless of which model is driving it. Only the *triggering* mechanism (Claude's skill system
vs. a pasted system prompt) differs per platform.

## Repository structure

```
jira-ticket-builder-skill/
├── skill/                       # Claude Skill (SKILL.md + assets + references)
│   ├── SKILL.md
│   ├── assets/
│   │   ├── full-template.md         # Full enterprise ticket template
│   │   ├── quick-template.md        # Quick-mode ticket template
│   │   ├── story-template.md        # Dedicated Story template
│   │   ├── portal-page-template.html # Shared multi-page portal template (with diagrams)
│   │   └── build_portal.py          # Generates the 12-page portal from decomposition JSON
│   └── references/
│       ├── section-guide.md         # Which full-template sections apply per issue type
│       └── decomposition-schema.md  # JSON schema for decomposition mode
├── prompt/
│   └── INSTRUCTIONS.md          # Portable version of SKILL.md for non-Claude LLMs
├── bin/
│   └── install.js               # npx installer
├── package.json
├── LICENSE
└── README.md
```

## Known limitation

The portal is a set of 12 linked HTML files using relative links between them
(`business-context.html`, `stories.html`, etc.). **Keep all 12 files together in one folder** —
if you only save one file in isolation, sidebar navigation between pages won't resolve. When the
skill generates a portal, it packages the output as a `.zip` for exactly this reason; extract it
before opening `index.html`.

## Contributing

Issues and PRs welcome once this is published — update the `repository`/`homepage`/`bugs` URLs in
`package.json` to point at your actual GitHub repo before publishing.

## License

MIT
