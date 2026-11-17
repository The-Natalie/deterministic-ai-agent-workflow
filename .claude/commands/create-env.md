---
description: Create the .env and .env.example files for this project from the PRD and plan
---

# Create Environment Files

Create the `.env` and `.env.example` files for this project.

Include all required environment variables based on the PRD and the implementation plan. Use values clearly marked as placeholders in both files. Make both files identical, including any helpful comments explaining each variable.

## Process

### 1. Check before writing

- If `.env` or `.env.example` already exists, stop and ask the user before doing anything. **Never overwrite or modify an existing `.env`**; it may hold real secrets.
- Confirm `.env` is ignored by git: run `git check-ignore .env`. If it is not ignored, add `.env` to `.gitignore` and say so.

### 2. Work out the variables

Read the sources and list every environment variable the project needs:

- `PRD.md` (integrations, services, databases, ports, API keys)
- the global rules file `AGENTS.md` (commands, stack, environment constraints)
- any implementation plans or build lists in `.agents/plans/`, if they exist yet
- `tools/reviewer.config.json`: include the API key variable named by the `api_key_env` of the active reviewer profile (and of any backup profile you expect to use), because the automatic plan and execution reviews need it

Do not invent variables the project does not need. For each one, decide a clearly fake placeholder value (for example `your-api-key-here`), never a real-looking secret.

### 3. Write both files

Create `.env.example` and `.env` with identical contents: the same variables, the same placeholder values, and the same comments. Group related variables and put a short comment above each one saying what it is for and where to get the value.

## Report

Tell the user:

- the path of both files and how many variables each contains (list them, with the one-line purpose of each)
- that the real values belong **only in `.env`**, never in `.env.example`, and that the placeholders must be replaced before running the project
- that `.env` is ignored by git (and whether you had to add it to `.gitignore`)
- which variable the reviewer needs, so the automatic plan and execution reviews can run

Do not fill in real values, and do not commit anything.
