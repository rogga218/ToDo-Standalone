---
name: dependency-checker
description: Check if frontend (Node/npm) and backend (Python/pip) dependencies are up to date. Produces a health report detailing outdated packages, semver bump types, security vulnerabilities, and safe update suggestions before applying any upgrades.
license: MIT
compatibility: Requires Python 3.10+ and Node.js / npm with PowerShell terminal environment.
metadata:
  author: Antigravity
  version: "1.0"
---

# Dependency Checker & Upgrade Advisor Skill

Use this skill to inspect, audit, and evaluate dependency versions across the entire project (both backend Python dependencies and frontend Node.js / Playwright dependencies).

## Core Principles

1. **Report First, Never Update Blindly:** Always present an assessment of what is outdated, breaking change risks, and security findings before modifying any files or running upgrade commands.
2. **Distinguish Version Risk Levels:**
   - 🟢 **Patch (x.x.Z):** Bug fixes and security patches. Safe to update.
   - 🟡 **Minor (x.Y.z):** Backward-compatible features. Generally safe, verify with tests.
   - 🔴 **Major (X.y.z):** Potential breaking changes. Requires code inspection and testing.
3. **Verify Everything:** Run the test and linting suite (`ruff`, `mypy`, `pytest`, `playwright`) after applying any updates.

---

## Step 1: Run the Automated Audit

Execute the automated checker script to inspect both ecosystems and produce a formatted Markdown report:

```powershell
.\.venv\Scripts\python.exe .agents\skills\dependency-checker\scripts\check_dependencies.py
```

### Manual CLI Inspection Equivalents

If you need to query either ecosystem individually:

- **Backend (Python / pip):**
  - List outdated packages:
    ```powershell
    .\.venv\Scripts\python.exe -m pip list --outdated
    ```
  - Run vulnerability scan:
    ```powershell
    pip-audit -r requirements.txt
    ```

- **Frontend (Node / npm):**
  - List outdated packages:
    ```powershell
    npm outdated
    ```
  - Run vulnerability scan:
    ```powershell
    npm audit
    ```

---

## Step 2: Present the Upgrade Report

When executing this skill, format the findings as a structured report containing:

1. **Summary Overview:**
   - Total backend packages checked vs outdated count.
   - Total frontend packages checked vs outdated count.
   - Security vulnerabilities identified (if any).

2. **Backend Table (`requirements.txt`):**
   - Columns: Package, Defined in `requirements.txt`, Currently Installed, Latest on PyPI, Bump Type (Major/Minor/Patch), Risk.

3. **Frontend Table (`package.json`):**
   - Columns: Package, Current, Wanted (within semver range), Latest npm, Bump Type, Risk.

4. **Security Advisories:**
   - Summarize CVEs, severity levels, and available fix versions.

5. **Phased Recommendations & Suggestions:**
   - **Phase 1 (Safe):** Group patch and minor releases with minimal breaking risk.
   - **Phase 2 (Careful / Breaking):** Flag major version bumps and dependencies known for API changes.
   - **User Prompt:** Explicitly ask the user whether they would like to proceed with Phase 1, Phase 2, or specific packages.

---

## Step 3: Applying Updates (Upon User Approval)

### For Backend Dependencies

1. Update the version specifier in `requirements.txt` (e.g. `fastapi>=0.162.0`).
2. Install the updated package into `.venv`:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade
   ```

### For Frontend Dependencies

1. For safe in-range updates:
   ```powershell
   npm update
   ```
2. For major/pinned upgrades:
   ```powershell
   npm install <package-name>@latest --save-dev
   ```

---

## Step 4: Verification Suite Mandate

Immediately after updating any dependencies, run the project verification suite to ensure zero regressions:

```powershell
ruff check src
ruff format src
mypy src
pytest -v
npx playwright test
```

