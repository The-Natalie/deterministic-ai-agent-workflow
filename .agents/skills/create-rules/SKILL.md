---
name: create-rules
description: Generate the project's AGENTS.md rules (and the CLAUDE.md pointer) using the existing Deterministic Workflow.
---

Read `.claude/commands/create-rules.md` and follow its discovery, analysis, generation, and reporting phases.

Notes:
1. `AGENTS.md` is the single source of project rules; `CLAUDE.md` only imports it with `@AGENTS.md`.
2. Use the existing root `AGENTS.md` as the structural template.
3. Do not invent dependencies, commands, architectural decisions, or coding conventions. Clearly distinguish planned architecture from patterns already implemented in code.
4. Preserve the original command's reporting format.

Do not implement application features.
