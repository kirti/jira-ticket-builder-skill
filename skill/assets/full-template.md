# Enterprise Jira Ticket Template

## 1. Ticket Metadata

**Issue Type:**
Bug / Story / Task / Spike / Tech Debt / Security / Incident

**Summary:**

> Clear, concise statement of the work or problem.

**Priority:**
Critical / High / Medium / Low

**Severity:**
S1 / S2 / S3 / S4

**Business Priority:**
High / Medium / Low

**Component / Service:**

> Application, service, module, or business capability affected.

**Team:**

> Owning engineering/product team.

**Labels:**

> `authentication`, `checkout`, `performance`

---

# 2. Business Context

## Problem Statement

> What problem are we solving?

## Business Impact

> Why does this matter to the business?

Include where applicable:

* Revenue impact
* Customer impact
* Operational impact
* Regulatory/compliance impact
* SLA/SLO impact
* Developer productivity impact

## User Impact

**Who is affected?**

> Customers / Internal users / Operations / Developers / Partners

**Impact:**

> Describe the customer or user experience.

---

# 3. Current Behavior

## What Happens Today?

> Describe the current behavior clearly and objectively.

## Expected Behavior

> Describe what should happen instead.

## Reproduction Steps

1. Step 1
2. Step 2
3. Step 3

**Expected:**

> ...

**Actual:**

> ...

---

# 4. Scope

## In Scope

* ...
* ...
* ...

## Out of Scope

* ...
* ...
* ...

## Assumptions

* ...
* ...

---

# 5. Technical Context

## Affected Systems

| System    | Component      | Impact |
| --------- | -------------- | ------ |
| Service A | Authentication | High   |
| Service B | Redis          | Medium |
| Database  | User Session   | Medium |

## Technical Details

> Relevant architecture, APIs, database, infrastructure, configuration, or implementation details.

## Suspected Root Cause

> Only include if confirmed.

## Possible Root Cause

> Clearly mark hypotheses as hypotheses.

## Affected Code / Configuration

```text
service/
  auth/
  session/
  config/
```

---

# 6. Proposed Solution

## Recommended Approach

> Describe the proposed implementation.

## Implementation Details

1. ...
2. ...
3. ...

## Alternatives Considered

### Option 1

> ...

### Option 2

> ...

**Recommended:** Option 1

**Reason:**

> ...

---

# 7. Acceptance Criteria

### AC1 — Primary Behavior

**Given** [precondition]
**When** [action]
**Then** [expected result]

### AC2 — Error Handling

**Given** [error condition]
**When** [action]
**Then** [expected behavior]

### AC3 — Existing Functionality

**Given** existing functionality
**When** the change is deployed
**Then** existing behavior remains unchanged.

### AC4 — Observability

**Given** the new implementation
**When** the relevant operation occurs
**Then** appropriate logs/metrics/traces are available.

---

# 8. Non-Functional Requirements

## Performance

> Expected response time / throughput / latency.

## Scalability

> Expected behavior under increased load.

## Availability

> Required availability / SLA / SLO.

## Security

* Authentication
* Authorization
* Data protection
* Secrets
* Input validation
* Audit requirements

## Compliance

> PCI / SOC2 / GDPR / HIPAA / regulatory requirements where applicable.

---

# 9. Testing Strategy

## Unit Tests

* ...
* ...

## Integration Tests

* ...
* ...

## API Tests

* ...
* ...

## End-to-End Tests

* ...
* ...

## Regression Tests

* ...

## Performance Tests

* ...

## Security Tests

* ...

---

# 10. Observability

## Logging

> What should be logged?

## Metrics

> What metrics should be monitored?

## Tracing

> Required distributed tracing / correlation IDs.

## Alerts

> What conditions should trigger an alert?

## Dashboard

> Existing or new dashboard.

---

# 11. Deployment & Release

## Deployment Strategy

> Standard / Feature Flag / Canary / Blue-Green / Phased

## Feature Flag

**Flag:** `...`

## Configuration Changes

* ...
* ...

## Database Changes

* Migration required: Yes / No
* Backward compatible: Yes / No

## Rollout Plan

1. ...
2. ...
3. ...

---

# 12. Rollback Plan

> Explain exactly how the change can be safely rolled back.

**Rollback Trigger:**

> ...

**Rollback Steps:**

1. ...
2. ...
3. ...

---

# 13. Dependencies

| Dependency | Type      | Owner  | Status  |
| ---------- | --------- | ------ | ------- |
| Service A  | Technical | Team A | Ready   |
| API B      | External  | Team B | Pending |

---

# 14. Risks

| Risk | Probability | Impact | Mitigation |
| ---- | ----------- | ------ | ---------- |
| ...  | Low         | High   | ...        |

---

# 15. Definition of Done

* [ ] Code implemented
* [ ] Unit tests added
* [ ] Integration tests added
* [ ] Acceptance criteria validated
* [ ] Code reviewed
* [ ] Security requirements validated
* [ ] Performance requirements validated
* [ ] Logging/metrics/tracing implemented
* [ ] Documentation updated
* [ ] Deployment validated
* [ ] Rollback plan verified
* [ ] Product owner acceptance completed

---

# 16. Traceability

**Parent Epic:**

> ...

**Related Stories:**

> ...

**Related Bugs:**

> ...

**Related PRs:**

> ...

**Related Design / ADR:**

> ...

**Related Incident:**

> ...

**Related Documentation:**

> ...

---

# 17. AI-Generated Information

**Generated By:** Jira Ticket Builder AI

**Source:**

> Meeting notes / Slack / User input / Incident / Repository analysis

**Confidence:**
High / Medium / Low

**AI-Inferred Information:**

> Explicitly identify information inferred by AI.

**Missing Information:**

> Information that should be confirmed before implementation.

**Human Approval Required:**
Yes / No
