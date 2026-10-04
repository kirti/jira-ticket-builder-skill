# Decomposition Output Schema

Decomposition mode (rough requirements doc → multiple stories) produces one JSON object matching
this schema. A machine-readable copy lives in `assets/decomposition.schema.json`, and
`assets/quality_gate.py` validates against it — if you change one, change the other. Keep it scoped — this is deliberately smaller than a full "architecture + UI +
backend + CI/CD" spec generator. Technical context lives *inside* each story, not as separate
top-level views.

```json
{
  "project": {
    "name": "string — inferred or user-provided",
    "source_summary": "1-2 sentence summary of what the rough doc was about",
    "generated_at": "ISO date",
    "business_objectives": [
      { "id": "OBJ-001", "text": "string", "confidence": "confirmed|inferred" }
    ],
    "business_actors": [
      { "id": "ACT-001", "name": "string — e.g. Customer, Support Agent", "description": "string" }
    ],
    "business_flow": [
      { "step": 1, "actor": "string", "action": "string", "system": "string — system touched, or 'none'", "ui_screen": "string — screen name if this step has a UI touchpoint, or omit/null", "api": "string — API called at this step, or omit/null" }
    ]
  },
  "business_requirements": [
    { "id": "BR-001", "text": "string", "source_excerpt": "verbatim-ish short excerpt or paraphrase pointer to source line", "confidence": "confirmed|inferred" }
  ],
  "functional_requirements": [
    { "id": "FR-001", "text": "string", "source_excerpt": "string", "confidence": "confirmed|inferred" }
  ],
  "non_functional_requirements": [
    { "id": "NFR-001", "text": "string", "category": "performance|security|accessibility|compliance|other", "confidence": "confirmed|inferred" }
  ],
  "business_rules": [
    { "id": "RULE-001", "text": "string", "story_ids": ["STORY-001"], "confidence": "confirmed|inferred" }
  ],
  "stories": [
    {
      "id": "STORY-001",
      "title": "string",
      "type": "Story|Technical Story|Spike|Enabler|Bug|Task",
      "business_capability": "string",
      "user_story": "As a ... I want ... so that ...",
      "description": "string",
      "decomposition_rationale": "string — why this is its own story rather than folded into another",
      "in_scope": ["string"],
      "out_of_scope": ["string"],
      "business_rule_ids": ["RULE-001"],
      "acceptance_criteria": [
        { "given": "string", "when": "string", "then": "string" }
      ],
      "technical_context": {
        "affected_systems": ["string"],
        "apis": [
          { "method": "GET", "path": "/api/accounts", "request": "string", "response": "string", "auth": "string" }
        ],
        "data": ["string"],
        "security": ["string"],
        "ui_spec": {
          "screen": "string — or 'n/a' if no UI surface",
          "components": ["string"],
          "fields": ["string"],
          "states": ["loading", "empty", "error", "success"],
          "navigates_to": [
            { "to": "string — target screen name", "trigger": "string — e.g. 'Select account', 'Back button'" }
          ]
        },
        "testing": {
          "unit": ["string"], "integration": ["string"], "api": ["string"], "e2e": ["string"]
        },
        "cicd": ["string — pipeline steps or requirements specific to this story"]
      },
      "dependencies": [
        { "story_id": "STORY-xxx", "relationship": "depends_on|blocks|relates_to", "reason": "string" }
      ],
      "open_question_ids": ["Q-001"],
      "source_requirement_ids": ["BR-001", "FR-002"],
      "completeness_pct": 0,
      "status": "Draft"
    }
  ],
  "open_questions": [
    {
      "id": "Q-001",
      "question": "string",
      "area": "Business|UI|Backend|Security|NFR|Data|CI/CD",
      "severity": "Critical|High|Medium|Low",
      "owner": "string — or 'Unassigned'",
      "impact": "string",
      "story_ids": ["STORY-001"],
      "origin": "stated|ai_identified",
      "status": "Open"
    }
  ],
  "assumptions": [
    { "id": "A-001", "text": "string", "story_ids": ["STORY-001"] }
  ],
  "decisions": [
    { "id": "D-001", "decision": "string", "owner": "string — or 'Unassigned'", "story_ids": ["STORY-001"], "status": "Proposed|Pending|Approved|Rejected" }
  ],
  "risks": [
    { "id": "R-001", "risk": "string", "impact": "High|Medium|Low", "probability": "High|Medium|Low", "story_ids": ["STORY-001"], "mitigation": "string" }
  ],
  "architecture": {
    "flow": ["User", "UI", "API", "Service", "Data"],
    "components": [
      { "name": "string", "type": "frontend|api|service|database|external", "description": "string" }
    ],
    "integration_points": [
      { "from": "string — component or flow node name", "to": "string — component or flow node name", "label": "string — e.g. 'REST, sync'", "type": "sync|async" }
    ]
  },
  "dependencies": [
    { "from": "STORY-002", "to": "STORY-001", "reason": "string" }
  ],
  "traceability": [
    { "requirement_id": "BR-001", "source_excerpt": "string", "story_ids": ["STORY-001"], "covered": true }
  ],
  "readiness": {
    "business_pct": 0,
    "requirements_pct": 0,
    "technical_context_pct": 0,
    "testing_pct": 0,
    "traceability_pct": 0,
    "story_completeness_avg_pct": 0
  }
}
```

## Rules for filling this out

- **Never invent a business_requirements/functional_requirements entry** that isn't traceable to
  something in the source doc. If you need a requirement to make a story coherent and it wasn't
  stated, that's an **assumption** or an **AI-identified open question**, not a requirement.
- **Every story must have at least one `source_requirement_ids` entry.** A story with no source
  link is a fabrication — don't emit it.
- **`confidence` fields** (on requirements, objectives, business rules): `"confirmed"` means it's
  stated in the source document; `"inferred"` means you concluded it from context. Default to
  `"inferred"` when in doubt — don't mark something confirmed unless you can point to source text.
- **`open_questions` with `origin: "ai_identified"`** are questions you inferred are necessary
  (e.g. "what's the expected response time?" when nothing about performance was stated) — mark
  these distinctly and never let them read as if the user asked them.
- **`severity` and `owner` on open questions**: severity is your assessment of how much this
  blocks implementation (Critical = blocks starting work; Low = nice to clarify eventually).
  `owner` should be `"Unassigned"` unless the source doc names who should answer it — never
  invent a name.
- **`decisions` and `risks` are opt-in, not mandatory filler.** Only emit a decision entry when
  the source doc shows an actual decision being made or requiring approval. Only emit a risk when
  there's a real, specific risk you can name — not generic boilerplate like "requirements may
  change." A short or empty risks/decisions list is fine and more honest than padding it.
- **`architecture`** stays structural/textual — a flow array, a components list, integration
  points. This is not a diagramming tool; don't try to encode visual layout, just the facts a
  reader needs.
- **`technical_context.ui_spec`** should be `"n/a"` for the screen field on stories with no UI
  surface (e.g. a pure backend/CI-CD story) rather than being force-filled. Set `navigates_to`
  whenever the screen leads somewhere else (including "back" navigation) — this drives the UI
  Flow diagram, so a screen with no `navigates_to` entries will render as a dead end.
- **`architecture.integration_points`** are structured `{from, to, label, type}` objects, not free
  text — `from`/`to` should match names used in `architecture.flow` or `architecture.components`
  exactly (case-sensitive) so the architecture diagram can resolve them. An integration point
  referencing a name not present in `flow` or `components` will render as an orphan edge.
- **`business_flow[].ui_screen` and `.api`** are optional and drive the Customer Journey diagram.
  Set `ui_screen` when a step has a screen the user is looking at (match a story's
  `ui_spec.screen` exactly), and `api` when the step involves an API/system call (a short
  `METHOD /path` string is fine — doesn't need to match a story's `apis` entry verbatim). Leave
  both unset for steps that are purely one system calling another with no UI or nameable API
  (e.g. an internal audit write) — the diagram renders those as an intentional gap in that lane,
  not an error.
- **`completeness_pct` per story and `readiness` percentages** are recomputed from the data by
  `build_portal.py` (pass `--model-metrics` to keep yours), so treat what you write as an
  estimate. The formulas, from `quality_gate.py`:
  - story completeness = share of 8 items present: user story, description, acceptance criteria,
    a source requirement, an in-scope list, technical context (affected systems or APIs), at least
    one test, and no open Critical/High question linked to the story;
  - `business_pct` = share of objectives / actors / business flow / business requirements present;
  - `requirements_pct` = share of requirements marked `confirmed`;
  - `technical_context_pct` / `testing_pct` = share of stories with technical context / tests;
  - `traceability_pct` = share of requirements cited by at least one story;
  - `story_completeness_avg_pct` = mean story completeness.
  Each traceability row's `covered` is likewise set from whether any story cites the requirement.
- Keep IDs stable and sequential (BR-001, BR-002...) so cross-references in the portal resolve.
