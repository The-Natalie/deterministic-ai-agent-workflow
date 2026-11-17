---
name: new-project
description: Create a new project from the starter system in the current (empty) folder.
---

Read `.claude/commands/new-project.md` and follow its instructions in order.

Argument handling:
- Treat `$ARGUMENTS` in the referenced command as the optional project name supplied with this skill invocation.
- Never treat the literal string `$ARGUMENTS` as a project name.

Never overwrite existing files, never commit, and never run outside an empty folder.
