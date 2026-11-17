Deterministic Agent Starter System

A reusable workflow and file system for building AI agents in a structured, repeatable way.

⸻

What this is

This is a starter system I use to build AI agents step by step using a deterministic workflow.

It's designed to be copied into a new project and used as the foundation for planning, implementation, testing, validation, and iteration. Instead of starting from scratch each time, this provides a consistent structure for how work is defined and completed.

⸻

Start Here (Step-by-Step Guide)

If you're new to this workflow, start with the guide: deterministic-agent-workflow-guide.pdf  

This is a complete, step-by-step process for building an AI agent from idea to implementation using this system.

It's designed to remove ambiguity by turning every step into a clear, actionable task, including planning, execution, testing, validation, and iteration.

If you follow the guide from start to finish, you'll go from a blank project to a fully built and validated system.

⸻

Why I built this

When I first started building with AI, I could get things working, but the process felt inconsistent. There wasn't a clear way to move from idea to implementation while knowing that each step was actually correct.

After discovering loop-based workflows, I built my own version that focuses on structure, validation, and control. I adapted the core idea, added stricter validation rules, and refined the process so it could be used reliably across different projects.

The goal is simple: remove ambiguity and make the system predictable.

⸻

How it works (high level)

The workflow follows a repeatable loop:

Select → Plan → Review → Execute → Review → Validate → Commit → Repeat

Each feature is built one small piece at a time, and nothing moves forward unless it is explicitly validated.

In practice, the commands run in this order:

/start-logging (once per project) → /prime → /plan-feature → automatic plan review → you approve the plan → /execute → automatic execution review → you verify → /commit

⸻

Key idea: deterministic validation

Most AI-assisted workflows rely on vague checks like:

"make sure it works"

This system does not.

Every requirement must map to:

* a command
* an exact expected output

If the output does not match, the work is not complete.

This removes interpretation and forces correctness to be visible.

⸻

Starting a new project

/new-project turns an empty folder into a new project built from this starter: it copies the starter files in (without the starter's git history, its /new-project command, or your personal settings), writes a blank README.md, runs git init on branch main, and starts conversation logging. It never commits and never overwrites anything.

One-time setup (so the command exists in every folder):

1. Link the command into your user-level commands folder:
   ln -s "<path to this starter>/.claude/commands/new-project.md" ~/.claude/commands/new-project.md
2. Tell it where the starter lives. Copy .agents/new-project/config.json to .agents/new-project/config.local.json (same folder) and put your real path in config.local.json. That file is gitignored, so your personal path never reaches GitHub. /new-project reads config.local.json first, then config.json, and asks you (and saves the answer to config.local.json) if neither has a valid path.

Then, for each new project: make an empty folder, open it in VS Code, start your agent there, and run /new-project. When it finishes, restart the agent in that folder so the project's own commands load.

To connect the project to GitHub: create an EMPTY repository on GitHub (no README), then run git remote add origin <repo-url> in the standard terminal. The first commit and push come later in the guide.

⸻

Environment files and running the app

* /create-env — creates .env and .env.example (identical, placeholders only) from the PRD and plan, including the API key your reviewer needs. It never overwrites an existing .env. Put real values only in .env.
* /start-dev — starts the app's dev server(s) in separate Terminal windows (macOS), waits until the app responds, and opens it in Chrome. Close the windows to stop. It reads the start command and URL from AGENTS.md and asks you if they are missing.
* /init-project — one-time setup (install dependencies, migrations). Use /start-dev for day-to-day running.

⸻

Key idea: automatic independent review

The model that builds the work is never the one that checks it.

When /plan-feature finishes a plan, a separate reviewer model automatically checks it against the PRD and the phase build list: are the requirements covered, is anything out of scope, does every acceptance criterion name a check with an exact expected result, are prerequisites accounted for. When /execute finishes, the reviewer checks the execution report against the plan and verifies the reported file changes against the real filesystem.

If the reviewer finds routine problems, it sends them back to the builder, the builder fixes them, and the reviewer checks again. This repeats up to 3 times per run. You are brought in only when:

* the reviewer approves (you do your final check)
* a decision is needed that only you can make (scope, architecture, ambiguous requirements)
* something is blocked (for example, a missing API key)
* the 3-cycle limit is reached

Each review ends with a short Stage Summary at the top of the review file, telling you the status, what was fixed, what remains, and your next action. The review commands (/review-plan and /review-execution) can also be run by hand to re-review after you edit something.

Where the files go:

* plan reviews: .agents/plans/reviews/<plan-name>-plan-review.md
* execution reports: .agents/execution-reports/<plan-name>-execution-report.md
* execution reviews: .agents/execution-reports/reviews/<plan-name>-execution-report-review.md

⸻

Choosing the reviewer model

Reviewer settings live in one file: tools/reviewer.config.json. It has named profiles:

* muse (default) — Meta's Muse Spark. Key: MODEL_API_KEY
* openai (backup) — gpt-5-mini by default (cheap but capable); change the model line in the file for a stronger one. Key: OPENAI_API_KEY
* claude — Claude via the Anthropic API. Key: ANTHROPIC_API_KEY

The reviewer should be a different model from your builder. If you build with Muse, use openai or claude as the reviewer; if you build with Claude, muse or openai.

To switch for good: open tools/reviewer.config.json and change the "active" line, for example "active": "openai".
To switch for one run only: set REVIEWER_PROFILE=openai in the environment, or add --profile openai when running a review script by hand.

API keys go in your shell environment or in the project's .env file (never committed).

⸻

Key idea: conversation logging

Every conversation you have with your coding agent, Muse or Claude Code, can be saved automatically to conversation-log/ at the project root, separate from the build output. It is gitignored because the logs contain everything you typed.

* /start-logging — run once per project, near the beginning. It starts a small background logger (macOS) that also restarts when you log in. You do not run it again each session.
* /stop-logging — run when the project is finished (or to pause). Logs already saved are kept.
* python3 tools/conversation-log.py status — shows whether logging is running for this project.
* python3 tools/conversation-log.py once — one-time catch-up if you did not start the background logger.

The logger only reads your agent's own session files. It makes no network calls and costs no tokens. One logger handles both tools: it records Muse sessions and Claude Code sessions for the project, labelled "Muse" or "Claude".

⸻

Key idea: system review

Most workflows improve the product. This one also improves itself.

After each implementation cycle, the system-review command compares what was planned against what was actually built. It classifies divergences as justified or problematic, traces root causes, and outputs concrete suggestions for updating AGENTS.md, plan commands, or automating repeated manual steps.

Process gaps are treated the same way as code bugs: found, documented, and fixed.

⸻

Built-in features and where to find their output

These features go beyond a basic plan-and-build loop. Most of them write files into your project as you work, so this is the quick reference for what each one does and where its output lands. Folders marked "generated" do not exist in the starter; they appear in your project the first time the feature runs.

Planning and records

* Prime summary and phase build list (/prime)
    What it does: summarizes the project's current state and writes the confirmed, ordered list of deliverables for the current phase. /plan-feature reads these to know exactly what to plan.
    Where: .agents/plans/prime-summary.md and .agents/plans/phase-{N}-build-list.md (generated)
* Feature plans (/plan-feature)
    What it does: one detailed plan per deliverable, including acceptance criteria that each name a check and its exact expected result.
    Where: .agents/plans/<plan-name>.md (generated). Corrections made by the review loop are logged at the bottom of the plan under "Revision History".
* Execution reports (/execute)
    What it does: records the full, verbatim output of everything the execution did: every command run, every line of test output, every validation result, and any deviation from the plan. It ends with an Evidence Map giving each acceptance criterion a status (VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, or FAILED) with the evidence behind it. This is the place to look for command output.
    Where: .agents/execution-reports/<plan-name>-execution-report.md (generated). One report per deliverable; it is never overwritten (execute stops and asks first if one exists).

Independent review

* Plan review (automatic at the end of /plan-feature; also /review-plan)
    What it does: a different model checks the plan against the PRD and the phase build list, then sends routine fixes back to the builder (up to 3 cycles). A Stage Summary at the top of the review gives the status, what was fixed, what remains, and your next action.
    Where: .agents/plans/reviews/<plan-name>-plan-review.md (generated)
* Execution review (automatic at the end of /execute; also /review-execution)
    What it does: a different model checks the execution report against the plan and verifies the reported file changes against the real filesystem. Corrections and their evidence are appended to the execution report under "Follow-up Validation (cycle N)".
    Where: .agents/execution-reports/reviews/<plan-name>-execution-report-review.md (generated)
* Reviewer model settings
    Where: tools/reviewer.config.json (see Choosing the reviewer model)

Logging

* Conversation log (/start-logging, /stop-logging)
    What it does: saves one Markdown file per session containing your prompts and the agent's replies, for both Muse and Claude Code. It records the conversation only. Command output, tool calls, file contents, and the agent's thinking are not included. For command and test output, use the execution reports above.
    Where: conversation-log/<date>_<session-id>.md at the project root (generated, gitignored because it contains everything you typed, including any secrets)
    Check it is running: python3 tools/conversation-log.py status

Running and testing the app

* Start the app (/start-dev)
    What it does: starts the dev server(s) in their own Terminal windows and opens the app in Chrome. Nothing is written to disk.
* End-to-end test (e2e-test skill)
    What it does: tests every user journey in a real browser and verifies database records when the project has a datastore.
    Where: screenshots in e2e-screenshots/ (generated, gitignored)
* Validation (validate)
    What it does: runs the project's tests, type checks, linting, and a runtime check using the commands declared in AGENTS.md and the plan, and reports pass/fail. Output appears in the terminal only.

Code and process review

* Code review (code-review, code-review-fix)
    What it does: pre-commit review for logic errors, security issues, and pattern compliance, with a follow-up command to fix what it finds.
    Where: .agents/code-reviews/ (generated)
* System review (system-review)
    What it does: compares what was planned against what was built and suggests fixes to the workflow itself.
    Where: .agents/system-reviews/<feature-name>-review.md (generated)
* Bug fix workflow (rca, implement-fix)
    What it does: investigates a GitHub issue and writes a root cause analysis, then implements the fix with regression tests.
    Where: docs/rca/issue-<number>.md (generated)

Project setup

* New project (/new-project): turns an empty folder into a new project from this starter. See Starting a new project.
* Environment files (/create-env): creates .env and .env.example from the PRD and plan. See Environment files and running the app.

⸻

Prerequisites

Required:

* A coding agent: Claude Code (claude.ai/code) and/or Muse
* git
* python3 (3.9 or newer) — runs the review and logging scripts in tools/
* An API key for the reviewer model you choose (see Choosing the reviewer model)

Optional, depending on the project and which parts of the workflow you use:

* Your project's own language runtime and package manager — e.g. Python + uv, Node + npm/pnpm/bun, Go, Rust
* npm — required only for the agent-browser skill and the e2e-test skill
* GitHub CLI (gh) — required only for the bug fix workflow (rca / implement-fix)
* Docker — only if your project needs backing services

⸻

How to use it

1. Create a new, empty folder for your project and open it in VS Code
2. Start your coding agent in that folder and run /new-project (see Starting a new project below)
3. Restart the agent in the folder so the project's commands load
4. Check tools/reviewer.config.json and set up the API key for your reviewer (/create-env adds the variable to .env)
5. Follow the step-by-step guide
6. Build one deliverable at a time using the workflow loop

Full step-by-step guide:
→ deterministic-agent-workflow-guide.pdf  

⸻

Repo structure

.claude/

Core command and skill layer used during development.

* commands/
    Slash commands that drive the workflow:
    /prime, /plan-feature, /execute, /create-prd, /create-rules, /commit,
    /review-plan, /review-execution (run automatically by /plan-feature and /execute),
    /start-logging, /stop-logging, /new-project, /create-env, /start-dev
* skills/
    Reusable capabilities for specific tasks:
    agent-browser — headless Chromium automation for web interaction, form filling, and screenshots
    e2e-test — end-to-end testing pipeline using parallel sub-agents and browser automation, for
    projects with a browser-accessible UI; includes database validation when the project has a datastore

⸻

.agents/

Planning, reference, and workflow support layer.

* agents/
    Specialized agent definitions with scoped system prompts.
    code-reviewer — reviews code against project standards including type safety, architecture
    compliance, structured logging conventions, and test coverage. Outputs structured reports.

* commands/
    Command suites for the core workflow and supporting flows:

    core_piv_loop/
        prime-tools

    validation/
        validate — runs the full deterministic gate: tests, type checking, linting, and a runtime
        check, using the commands the project declares in AGENTS.md and the feature plan
        code-review — pre-commit technical review for logic errors, security issues, and pattern compliance
        code-review-fix — implements fixes from a code review report and re-validates
        execution-report — structured output of what was built, test results, and plan divergences
        system-review — meta-level process analysis that treats workflow gaps as bugs to fix

    github_bug_fix/
        rca — fetches a GitHub issue, investigates root cause, and produces a structured RCA document
        implement-fix — implements the fix from an RCA document, writes regression tests, and validates

* reference/
    Architecture patterns, tool design guides, and implementation references.

* articles/
    Supporting documentation and deeper explanations.

* skills/
    Thin wrappers that let Muse run the workflow commands. Each one points at the matching
    file in .claude/commands/, which is the single source of truth for both agents.

* execution-reports/
    Verbatim outputs from each execution run: every command, every line of test output, every
    validation result, and any deviations from the plan. Reviews go in execution-reports/reviews/.

Note: some output directories (plans/, plans/reviews/, code-reviews/, system-reviews/) are generated
when the system is used and are not included in the starter repo.

⸻

tools/

Scripts the workflow runs for you (Python, standard library only).

* review-plan.py, review-execution.py — the independent reviewers used by /review-plan and /review-execution
* reviewer.config.json — which reviewer model to use (see Choosing the reviewer model)
* conversation-log.py — the conversation logger behind /start-logging and /stop-logging

⸻

.agents/new-project/

config.json (public placeholder) and config.local.json (your real starter path, gitignored) used by /new-project.

⸻

Root files

* AGENTS.md
    Global rules and conventions that guide how the agent builds and behaves. This is the single
    source of rules for every coding agent (Muse reads it directly).
* CLAUDE.md
    A small file for Claude Code that imports AGENTS.md (the line @AGENTS.md) so both agents follow
    the same rules. Put instructions here only if they apply to Claude Code alone.
* .env / .env.example
    Environment configuration. These are not shipped with the starter system — the workflow
    creates them for each project.

⸻

What this is good for

* building agent-based systems step by step
* reducing silent errors and unclear outcomes
* working through complex workflows in a controlled way
* making AI behavior more predictable
* improving the workflow itself over time, not just the product

⸻

What this is not

* a plug-and-play framework
* a fully automated system

It still requires judgment and understanding.
This provides structure, not decisions.

⸻

Notes

This workflow continues to evolve as I use it in real projects. Each iteration helps refine the system and improve reliability.
