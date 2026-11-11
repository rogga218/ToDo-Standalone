---
name: github-workflow
description: Perform Git and GitHub operations including checking repository status, staging, committing with conventional messages, pushing changes, and managing Pull Requests. Use this skill when asked to commit code, push to remote, manage branches, or interact with GitHub workflows.
license: MIT
compatibility: Requires Git and PowerShell terminal environment.
metadata:
  author: Antigravity
  version: "1.0"
---

# GitHub Workflow Skill

Use this skill when interacting with Git version control and GitHub remote operations for this repository.

## Pre-Commit Verification Mandate

Before staging or committing any code changes, **always** run the mandatory verification suite:

```powershell
ruff check src
ruff format src
mypy src
pytest -v -m "not gui"
```

Do not commit code if linting, type-checking, or tests fail!

## Conventional Commit Messages

Follow Conventional Commit guidelines for clear, structured commit messages:

- **`feat:`** A new feature (e.g. `feat: add Swedish localization to person dialog`)
- **`fix:`** A bug fix (e.g. `fix: resolve detached DB session in todo service`)
- **`docs:`** Documentation changes (e.g. `docs: update README with CI status badge`)
- **`chore:`** Maintenance / cleanup tasks (e.g. `chore: purge stale pycache and old test reports`)
- **`refactor:`** Code changes that neither fix a bug nor add a feature (e.g. `refactor: simplify UI controller state handling`)
- **`test:`** Adding or updating test cases (e.g. `test: add unit tests for person CRUD endpoints`)

## Core Git Commands

- **Check repository status:** `git status`
- **Check pending diffs:** `git diff`
- **Stage specific files:** `git add <file1> <file2>`
- **Commit changes:** `git commit -m "<type>: <description>"`
- **Push to remote:** `git push origin <branch_name>`
- **Create feature branch:** `git checkout -b feature/<feature_name>`

## Safety Rules

1. Never use `git add .` blindly if untracked temporary files exist; inspect `git status` first.
2. Never commit secrets, `.env` files with private keys, or SQLite `.db` database files.
3. Always verify that `.gitignore` ignores runtime cache files before committing.
