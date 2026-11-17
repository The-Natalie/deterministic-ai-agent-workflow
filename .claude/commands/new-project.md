---
description: Create a new project from the starter system in the current (empty) folder
argument-hint: [project-name]
---

# New Project

Turn the current, empty folder into a new project built from the starter system: copy the starter files in, give the project a blank README and its own fresh git repository, and start conversation logging. Run this first, in a new empty folder, before anything else.

**Never overwrite anything. Never commit. Never run this inside the starter folder or inside a project that already has files.**

## Step 1: Check the current folder

Run `ls -A`. The folder must be empty, ignoring only `.DS_Store` and `.vscode`. If anything else is present, stop and tell the user this command only runs in an empty folder.

## Step 2: Find the starter system

Find the starter's config folder (`.agents/new-project/` inside the starter), then read the starter path from it.

1. Locate the config folder:
   - If `~/.claude/commands/new-project.md` is a link (`readlink ~/.claude/commands/new-project.md`), the starter folder is two levels above that link's target (target is `<starter>/.claude/commands/new-project.md`).
   - Otherwise, if the user passed a path, or you are told where the starter is, use that.
   - Otherwise ask the user for the path to the starter system folder.
2. In `<starter>/.agents/new-project/`, read `starter_path` using these rules:
   - Look for `config.local.json` first and use your personal pathname if it exists.
   - If it doesn't exist, check the public `config.json`.
   - If neither provides a valid pathname, ask the user for it and save it to `config.local.json`.
3. A pathname is valid only if that folder exists and contains `AGENTS.md` and `.claude/commands/prime.md`. The placeholder `<path-to-your-starter>` is never valid.

Tell the user which starter folder you will copy from.

## Step 3: Get the project name

Use the argument if one was given. Otherwise use the current folder's name, and confirm it with the user in one short question. The name becomes the README title.

## Step 4: Copy the starter files

Copy everything from the starter into the current folder, leaving out what must not travel into a project:

```bash
rsync -a \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude '__pycache__' \
  --exclude '.env' \
  --exclude 'conversation-log' \
  --exclude '.claude/commands/new-project.md' \
  --exclude '.agents/skills/new-project' \
  --exclude '.agents/new-project' \
  "<starter>/" ./
```

If `rsync` is not available, copy with `cp -R` and then delete the same items from the copy. Never touch the starter itself.

## Step 5: Blank README

Replace `README.md` with:

```
# <Project Name>

_Describe your project here._
```

## Step 6: Fresh git repository

```bash
git init -b main
```

Do not add a remote and do not commit. The copy has no history and no connection to the starter's repository.

## Step 7: Start conversation logging

Run `python3 tools/conversation-log.py start` (the same as `/start-logging`).

## Step 8: Report

Tell the user, briefly:

- the project folder, the starter it was copied from, and that the README is blank
- that a new git repository on branch `main` was created, with no remote and no commits
- **restart needed:** the project's own commands (`/prime`, `/plan-feature`, and so on) load when Claude starts, so exit and run `claude` again in this folder before continuing (for Muse, start a new session)
- **before the first push:** create an EMPTY repository on GitHub (no README), then in the standard terminal run `git remote add origin <repo-url>`; the first commit and `git push -u origin main` come later, in the guide's "Make First Commit" section
- the next step in the guide: describe the project and ask the research and clarification questions
