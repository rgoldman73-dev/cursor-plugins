---
name: setup-pstack
description: Configure pstack model roles for this Claude Code or Codex project using models confirmed by the current host.
---

Before this workflow, read [the claude host adapter](../../references/host-adapter.md). It defines tool, model, history, and scheduling compatibility for this port.

# Setup pstack

1. Read the host adapter and any existing project `.pstack/models.json`. Detect models and supported effort values from the current session's documented capabilities. If unavailable, use `inherit-parent`; ask for a specific model only when the user wants one.
2. Ask for the user's budget preference (small, medium, large, or unlimited) and any role changes. Budget labels express preferences, not model IDs or a promise of a supported effort level. Keep the parent model unless the user requests a change. Panel defaults are three independent seats on the parent model.
3. Show the proposed role table. Confirm real IDs are available for this host. Store reasoning effort separately from model identity and omit it when unsupported. Never reuse Cursor model slugs merely because they appeared in upstream examples.
4. Write `.pstack/models.json` in the current project. Preserve unrelated fields, replace configured role values idempotently, and never change global Claude or Codex settings. Use this shape:

```json
{
  "budget": "medium",
  "defaultModel": "inherit-parent",
  "roles": {
    "feature, refactoring": "inherit-parent",
    "bug-fix": "inherit-parent",
    "perf-issue": "inherit-parent",
    "hillclimb": "inherit-parent",
    "judgment and prose": "inherit-parent",
    "hardest tasks": "inherit-parent",
    "how explorer": "inherit-parent",
    "how explainer": "inherit-parent",
    "why investigators": "inherit-parent",
    "why synthesizer": "inherit-parent",
    "reflect tooling": "inherit-parent",
    "reflect judgment, divergent, synthesizer": "inherit-parent",
    "arena runners": ["inherit-parent", "inherit-parent", "inherit-parent"],
    "arena cross-judge pool": ["inherit-parent", "inherit-parent", "inherit-parent"],
    "swarm workers": "inherit-parent",
    "architect runners": ["inherit-parent", "inherit-parent", "inherit-parent"],
    "interrogate reviewers": ["inherit-parent", "inherit-parent", "inherit-parent"]
  }
}
```

5. Report the file and confirmed capabilities. Later pstack workflows read this file explicitly; it is not an always-applied global rule. Offer a project verification skill if the repository lacks a way to drive the real app.
