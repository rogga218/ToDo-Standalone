---
description: Commit and Push Workflow
---

# Commit and Push Workflow

Follow this step-by-step workflow to safely verify, stage, commit, and push code changes to GitHub.

## Step 1: Inspect Pending Changes
Run `git status` and `git diff` to inspect modified, untracked, or deleted files:
```powershell
git status
```

## Step 2: Run Verification Suite
Run all mandatory linting, formatting, type checking, and unit testing commands:
```powershell
ruff check src
ruff format src
mypy src
pytest -v -m "not gui"
```
> ⚠️ **Stop Condition:** If any step fails, fix all errors before proceeding to stage or commit.

## Step 3: Stage Files
Stage only the files relevant to the current change (avoid adding unexpected untracked artifacts):
```powershell
git add <file1> <file2>
```

## Step 4: Commit with Conventional Message
Write a clear, concise commit message following conventional commit standards (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`):
```powershell
git commit -m "<type>: <brief description of changes>"
```

## Step 5: Push to Remote
Push the committed changes to the active branch on GitHub:
```powershell
git push origin <current_branch>
```

## Step 6: Confirm Remote Status
Verify that the push succeeded and inspect `git status`:
```powershell
git status
```
