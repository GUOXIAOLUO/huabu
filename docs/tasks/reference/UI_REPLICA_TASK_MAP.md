# UI Replica Wave — Task Card Map

This file is informational only. It does **not** authorize implementation. `AGENT_NEXT_TASK.md` remains the single task-selection authority.

## Entry / Exit

```text
R10-08 DONE + independent Review/Gate PASS
    ↓
UX-01 → UX-02 → ... → UX-15
    ↓
UX-15 independent Review PASS
    ↓
R11-01 may be activated
```

## Cards

| Card | Purpose | Primary references |
|---|---|---|
| UX-01 | Visual baseline + tokens | Canvas spec / canvas-overview |
| UX-02 | Canvas surface | canvas-overview |
| UX-03 | NodeShell | node spec / task-llm |
| UX-04 | Ports + edges | interaction / node-picker |
| UX-05 | Floating toolbar | media-editor / canvas-overview |
| UX-06 | Node Picker | node-picker |
| UX-07 | Connect-to-Create | node-picker |
| UX-08 | Parameter hierarchy | generation-node |
| UX-09 | Task / LLM | task-llm-node |
| UX-10 | Asset / media | media-editor |
| UX-11 | Collection / table | collection-table |
| UX-12 | Result workspace | result-workspace |
| UX-13 | Generic generation + provider/model UI | generation-node / provider-settings |
| UX-14 | ComfyUI builder | comfy-mapping |
| UX-15 | Acceptance + duplicate-owner gate | acceptance checklist / all refs |

## Hard Rules

- No card is executable because it exists in backlog.
- Exactly one active card.
- One card per Agent run.
- Independent Review before archive/activation of the next card.
- UI reference files are requirements/evidence, never task-selection authority.
- Do not start the UX wave before R10-08 + R10 gate PASS.
- Do not start R11-01 before UX-15 Review PASS.
