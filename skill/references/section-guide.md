# Section Guide: Adapting the Full Template by Issue Type

The full template (`assets/full-template.md`) has 17 sections. Not all sections are relevant to
every issue type. Use this guide to decide what to keep, trim, or drop. When trimming a section,
remove it entirely rather than leaving an empty placeholder — an adapted ticket should read as
intentionally scoped, not incomplete.

Always keep, regardless of type: **1 (Metadata), 2 (Business Context), 7 (Acceptance Criteria),
15 (Definition of Done), 17 (AI-Generated Information)**.

## Bug

Full weight on all sections. Bugs are the template's native case — use it close to as-is
(this is what the original example ticket in this skill was built for). Section 3 (Current vs
Expected Behavior + Repro Steps) is mandatory.

## Incident

Same as Bug, but front-load section 2 (Business Impact) and section 12 (Rollback Plan) —
these matter most under time pressure. Add a `**Detected At:**` and `**Resolved At:**`
timestamp pair to section 1 if known. Section 16 should always link the triggering incident
if one exists.

## Story

**Stories use their own dedicated template — `assets/story-template.md` — not this one.**
Do not adapt `full-template.md` for stories; its section order and framing (Current Behavior,
Suspected Root Cause, Rollback Plan as a first-class section, etc.) are built around bugs and
incidents and read as backwards or irrelevant when forced onto new-feature work. The story
template instead opens with the As-a/I-want/So-that framing, frames the problem as current vs.
desired state rather than "current behavior," and treats demoable acceptance criteria and
success metrics as the core of the ticket rather than an afterthought.

## Task

Trim heavily. Tasks are usually well-understood, low-ambiguity work. Keep Sections 1, 2
(brief), 4 (Scope), 7, 15. Drop Sections 3, 6 (Alternatives Considered), 8, 9 (unless the task
has real test surface), 10, 12, 14 unless the task specifically warrants them.

## Spike

Replace Section 6 (Proposed Solution) with a "Research Questions" list — a spike's job is to
answer questions, not implement a fix. Section 7 (Acceptance Criteria) should define what
"spike is done" looks like (e.g., "a written recommendation exists," not a shipped feature).
Drop Sections 11 (Deployment), 12 (Rollback), 13 (Dependencies) unless relevant.

## Tech Debt

Keep Section 2 (Business Context) focused on *why now* — tech debt tickets die in backlogs
without a clear cost-of-inaction argument. Keep Sections 5 (Technical Context), 6, 9, 14.
Drop Section 3 (no user-facing "current behavior" to describe, usually) unless the debt is
causing observable symptoms.

## Security

Full weight on all sections, plus: Section 8 (Security) is mandatory and should be the most
detailed section in the ticket, not boilerplate. Consider whether the ticket should be marked
private/restricted in Jira — flag this explicitly to the user rather than assuming.

---

## Quick mode

Quick mode (`assets/quick-template.md`) does not use this per-type adaptation — it's already
minimal. The only type-specific adjustment in quick mode is whether "Steps to Reproduce" is
included (bugs/incidents) or omitted (stories/tasks/spikes/tech debt).
