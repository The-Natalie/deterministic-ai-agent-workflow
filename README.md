Deterministic Agent Starter System

A reusable workflow and file system for building AI agents in a structured, repeatable way.

⸻

What this is

This is a starter system I use to build AI agents step by step using a deterministic workflow.

It’s designed to be copied into a new project and used as the foundation for planning, implementation, validation, and iteration. Instead of starting from scratch each time, this provides a consistent structure for how work is defined and completed.

⸻

Start Here (Step-by-Step Guide)

If you’re new to this workflow, start with the guide: deterministic-agent-workflow-guide.pdf  

This is a complete, step-by-step process for building an AI agent from idea to implementation using this system.

It’s designed to remove ambiguity by turning every step into a clear, actionable task, including planning, execution, validation, and iteration.

If you follow the guide from start to finish, you’ll go from a blank project to a fully built and validated system.

⸻

Why I built this

When I first started building with AI, I could get things working, but the process felt inconsistent. There wasn’t a clear way to move from idea to implementation while knowing that each step was actually correct.

After discovering loop-based workflows, I built my own version that focuses on structure, validation, and control. I adapted the core idea, added stricter validation rules, and refined the process so it could be used reliably across different projects.

The goal is simple: remove ambiguity and make the system predictable.

⸻

How it works (high level)

The workflow follows a repeatable loop:

Select → Plan → Execute → Validate → Commit → Repeat

Each feature is built one small piece at a time, and nothing moves forward unless it is explicitly validated.

⸻

Key idea: deterministic validation

Most AI-assisted workflows rely on vague checks like:

“make sure it works”

This system does not.

Every requirement must map to:

* a command
* an exact expected output

If the output does not match, the work is not complete.

This removes interpretation and forces correctness to be visible.

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
    Slash commands like /prime, /plan-feature, /execute, /create-prd, and /create-rules.
    These drive the workflow and control how the agent behaves.
* skills/
    Reusable capabilities for specific tasks such as browser-based actions and end-to-end testing.

⸻

.agents/

Planning, reference, and workflow support layer.

* plans/
    Generated outputs such as project summaries, prime summaries, and feature plans.
* commands/
    Supporting commands for the core workflow, validation, and bug-fix flows.
* reference/
    Architecture patterns, tool design guides, and implementation references.
* articles/
    Supporting documentation and deeper explanations.
* execution-reports/
    Outputs generated during execution and validation.

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

⸻

What this is not

* a plug-and-play framework
* a fully automated system

It still requires judgment and understanding.
This provides structure, not decisions.

⸻

Notes

This workflow continues to evolve as I use it in real projects. Each iteration helps refine the system and improve reliability.