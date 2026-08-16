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

Select → Plan → Execute → Test → Validate → Commit → Repeat

Each feature is built one small piece at a time, and nothing moves forward unless it is explicitly validated.

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

Key idea: system review

Most workflows improve the product. This one also improves itself.

After each implementation cycle, the system-review command compares what was planned against what was actually built. It classifies divergences as justified or problematic, traces root causes, and outputs concrete suggestions for updating CLAUDE.md, plan commands, or automating repeated manual steps.

Process gaps are treated the same way as code bugs: found, documented, and fixed.

⸻

Prerequisites

Before using this system, make sure you have the following installed:

* Claude Code — claude.ai/code
* Python + uv — for building Python/FastAPI agents
* npm — required for the agent-browser E2E testing tool
* GitHub CLI (gh) — required for the bug fix workflow

⸻

How to use it

1. Copy this starter system into a new project folder
2. Open the project in VS Code
3. Follow the step-by-step guide
4. Build one deliverable at a time using the workflow loop

Full step-by-step guide:
→ deterministic-agent-workflow-guide.pdf  

⸻

Repo structure

.claude/

Core command and skill layer used during development.

* commands/
    Slash commands that drive the workflow:
    /prime, /plan-feature, /execute, /create-prd, /create-rules, /commit
* skills/
    Reusable capabilities for specific tasks:
    agent-browser — headless Chromium automation for web interaction, form filling, and screenshots
    e2e-test — end-to-end testing pipeline using parallel sub-agents, browser automation, and database validation

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
        prime, plan-feature, execute, prime-tools

    validation/
        validate — runs the full deterministic gate: tests, type checking, linting, live server smoke test
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

* execution-reports/
    Verbatim outputs from each execution run: every command, every line of test output, every
    validation result, and any deviations from the plan.

Note: some output directories (plans/, code-reviews/, system-reviews/) are generated when the
system is used and are not included in the starter repo.

⸻

Root files

* CLAUDE.md
    Global rules and conventions that guide how the agent builds and behaves.
* .env / .env.example
    Environment configuration for each project.

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
