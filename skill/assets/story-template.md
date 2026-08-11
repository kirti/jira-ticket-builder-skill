# Enterprise Jira Story Template

## 1. Story Metadata

**Issue Type:**
Story

**Title:**

> Short, outcome-oriented title. Not "Add X button" — "Users can filter their order history by date"

**User Story:**

> **As a** [type of user]
> **I want** [capability/goal]
> **So that** [benefit/value]

**Priority:**
Critical / High / Medium / Low

**Story Points / Estimate:**

> ...

**Business Priority:**
High / Medium / Low

**Component / Service:**

> Application, service, module, or business capability affected.

**Team:**

> Owning engineering/product team.

**Labels:**

> `onboarding`, `checkout`, `mobile`

---

# 2. Why This Story Exists

## Problem / Opportunity

> What user or business problem does this address? What's the evidence (user feedback, data,
> support tickets, strategic goal)?

## Business Value

Include where applicable:

* Revenue impact
* Customer impact / satisfaction
* Retention / engagement impact
* Strategic alignment (OKR, roadmap theme)
* Competitive/market context

## Who Benefits

**Primary users:**

> Which user segment(s) get this capability?

**Value to them:**

> Describe the before/after from the user's perspective.

---

# 3. Current State vs. Desired State

## Current State

> What can users do (or not do) today? Frame as absence of capability, not as a "bug" —
> a Story is net-new value, not a correction.

## Desired State

> What will users be able to do once this ships?

## User Flow / Journey

1. Step 1 — entry point
2. Step 2 — core interaction
3. Step 3 — outcome/confirmation

> Include a rough sketch, wireframe link, or written walkthrough of the intended experience
> if available.

---

# 4. Scope

## In Scope

* ...
* ...
* ...

## Out of Scope

> Explicitly name what this story does NOT cover — this is often more important than "in scope"
> for stories, since scope creep is the main risk.

* ...
* ...

## Assumptions

* ...
* ...

## Open Design Questions

> Anything not yet decided — UX details, edge case handling, copy — that needs an answer before
> or during implementation.

* ...

---

# 5. Technical Context

## Affected Systems

| System    | Component | Impact |
| --------- | --------- | ------ |
| ...       | ...       | ...    |

## Technical Approach

> High-level implementation approach. Link to design doc/ADR if one exists rather than
> duplicating it here.

## New vs. Reused Components

> What's being built new vs. what existing components/services/APIs this leans on.

---

# 6. Acceptance Criteria

> Acceptance criteria for a story should be written from the user's perspective and should be
> demoable — someone should be able to watch a demo and check each one off.

### AC1 — Core Happy Path

**Given** [starting context]
**When** [user does the primary action]
**Then** [user achieves the described goal]

### AC2 — Edge Case / Alternate Path

**Given** [alternate context]
**When** [user does the action]
**Then** [expected handling]

### AC3 — Empty / Error States

**Given** [no data / invalid input / failure condition]
**When** [user encounters it]
**Then** [expected graceful behavior]

### AC4 — Existing Functionality Unaffected

**Given** existing related functionality
**When** this story is deployed
**Then** existing behavior remains unchanged

*(Add more ACs as needed — a story with only one AC is usually under-specified.)*

---

# 7. Non-Functional Requirements

## Performance

> Any expectations (load time, responsiveness) — omit if genuinely not applicable.

## Accessibility

> WCAG considerations, screen reader support, keyboard navigation, if relevant.

## Security & Privacy

> New data collected/stored, permissions required, PII considerations.

## Localization

> Does this need to support multiple languages/locales at launch?

---

# 8. Testing Strategy

## Unit Tests

* ...

## Integration Tests

* ...

## Manual / Exploratory Testing

* ...

## Usability / UAT

> Who reviews this before release — design, PM, a beta user group?

---

# 9. Rollout

## Release Strategy

> Full launch / Feature flag / Phased rollout / Beta group

## Feature Flag

**Flag:** `...` *(if applicable)*

## Success Metrics

> How will you know this story delivered the intended value post-launch? Name the specific
> metric(s) and, if known, the target.

## Rollback Plan

> Only needed if this is flagged or risky — for a low-risk additive story this can be brief
> or omitted.

---

# 10. Dependencies

| Dependency | Type      | Owner | Status |
| ---------- | --------- | ----- | ------ |
| ...        | Design    | ...   | ...    |
| ...        | Technical | ...   | ...    |

---

# 11. Definition of Done

* [ ] Code implemented
* [ ] Unit tests added
* [ ] Acceptance criteria demoed and validated
* [ ] Code reviewed
* [ ] Design/UX reviewed against mockups
* [ ] Accessibility checked
* [ ] Analytics/success metrics instrumented
* [ ] Documentation updated (user-facing and/or internal)
* [ ] Feature flag configured (if applicable)
* [ ] Product owner acceptance completed

---

# 12. Traceability

**Parent Epic:**

> ...

**Related Stories:**

> ...

**Related Design / Mockups:**

> ...

**Related Design / ADR:**

> ...

**Related Documentation:**

> ...

---

# 13. AI-Generated Information

**Generated By:** Jira Ticket Builder AI

**Source:**

> Meeting notes / Slack / User input / Product brief / Repository analysis

**Confidence:**
High / Medium / Low

**AI-Inferred Information:**

> Explicitly identify information inferred by AI (e.g. story points, business value framing,
> user segment).

**Missing Information:**

> Information that should be confirmed before implementation (e.g. exact design, success
> metric targets, rollout strategy).

**Human Approval Required:**
Yes / No
