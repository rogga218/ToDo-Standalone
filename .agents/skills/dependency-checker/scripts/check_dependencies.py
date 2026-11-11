"""Dependency checker script for ToDo Standalone.

Checks both Backend (Python/pip) and Frontend (Node/npm) dependencies for:
1. Outdated packages (Current vs. Latest vs. Defined in requirements.txt/package.json)
2. Semantic version bump type (Major, Minor, Patch)
3. Known security vulnerabilities (npm audit, pip-audit)
"""

import json
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_semver(version_str: str) -> Tuple[int, ...]:
    """Extract integer components of a version string."""
    clean = re.sub(r"^[^\d]*", "", version_str)
    parts = re.split(r"[.\-+]", clean)
    nums = []
    for p in parts:
        if p.isdigit():
            nums.append(int(p))
        else:
            break
    return tuple(nums) if nums else (0,)


def classify_bump(current: str, latest: str) -> Tuple[str, str]:
    """Classify version difference into Major, Minor, Patch, or Up-to-date."""
    c_parts = parse_semver(current)
    l_parts = parse_semver(latest)

    if not c_parts or not l_parts or c_parts == l_parts:
        return "Up-to-date", "🟢 Low"

    c_major = c_parts[0] if len(c_parts) > 0 else 0
    l_major = l_parts[0] if len(l_parts) > 0 else 0
    if l_major > c_major:
        return "Major", "🔴 High (Breaking Changes)"

    c_minor = c_parts[1] if len(c_parts) > 1 else 0
    l_minor = l_parts[1] if len(l_parts) > 1 else 0
    if l_minor > c_minor:
        return "Minor", "🟡 Medium (Features)"

    c_patch = c_parts[2] if len(c_parts) > 2 else 0
    l_patch = l_parts[2] if len(l_parts) > 2 else 0
    if l_patch > c_patch:
        return "Patch", "🟢 Low (Bugfixes)"

    return "Other", "⚪ Info"


def get_pypi_latest(package_name: str) -> Optional[str]:
    """Fetch the latest release version from PyPI API."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-DependencyChecker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                version = data.get("info", {}).get("version")
                return str(version) if version is not None else None
    except Exception:
        pass
    return None


def parse_requirements_file(file_path: Path) -> List[Dict[str, str]]:
    """Parse requirement specs from a requirements file."""
    packages: List[Dict[str, str]] = []
    if not file_path.exists():
        return packages

    lines = file_path.read_text(encoding="utf-8").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Match package name and version specifier (e.g. pkg>=1.0.0 or pkg==1.0.0)
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)(?:([=><~^!]+)(.*))?$", line)
        if match:
            pkg_name = match.group(1).strip()
            operator = match.group(2).strip() if match.group(2) else ""
            version = match.group(3).strip() if match.group(3) else ""
            packages.append({"package": pkg_name, "defined_spec": line, "operator": operator, "version": version})
    return packages


def check_python_dependencies(project_root: Path, filename: str = "requirements.txt") -> List[Dict[str, Any]]:
    """Check Python dependencies in the specified requirements file."""
    req_file = project_root / filename
    packages = parse_requirements_file(req_file)

    # Also retrieve currently installed packages in the python environment
    installed: Dict[str, str] = {}
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "list", "--format=json"], text=True, timeout=10, stderr=subprocess.DEVNULL
        )
        for item in json.loads(out):
            installed[item["name"].lower().replace("_", "-")] = item["version"]
    except Exception:
        pass

    # Fetch latest PyPI versions in parallel
    names = [item["package"] for item in packages]
    latest_versions: Dict[str, Optional[str]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(get_pypi_latest, name): name for name in names}
        for future in futures:
            name = futures[future]
            try:
                latest_versions[name] = future.result()
            except Exception:
                latest_versions[name] = None

    results = []
    for item in packages:
        name = item["package"]
        key = name.lower().replace("_", "-")
        installed_ver = installed.get(key, item["version"] or "N/A")
        latest_ver = latest_versions.get(name) or "Unknown"

        bump, risk = classify_bump(installed_ver, latest_ver) if latest_ver != "Unknown" else ("Unknown", "⚪ Unknown")
        results.append(
            {
                "package": name,
                "defined": item["defined_spec"],
                "installed": installed_ver,
                "latest": latest_ver,
                "bump": bump,
                "risk": risk,
                "is_installed": key in installed,
            }
        )
    return results


def check_node_dependencies(project_root: Path) -> List[Dict[str, Any]]:
    """Check Node.js frontend dependencies via npm outdated."""
    pkg_json_file = project_root / "package.json"
    if not pkg_json_file.exists():
        return []

    results = []
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    try:
        proc = subprocess.run(
            f"{npm_cmd} outdated --json", cwd=str(project_root), capture_output=True, text=True, timeout=15, shell=True
        )
        if proc.stdout:
            data = json.loads(proc.stdout)
            for pkg_name, info in data.items():
                current = info.get("current", "N/A")
                wanted = info.get("wanted", "N/A")
                latest = info.get("latest", "N/A")
                bump, risk = classify_bump(current, latest)
                results.append(
                    {
                        "package": pkg_name,
                        "current": current,
                        "wanted": wanted,
                        "latest": latest,
                        "bump": bump,
                        "risk": risk,
                    }
                )
    except Exception:
        pass

    return results


def run_security_audits(project_root: Path) -> Dict[str, Any]:
    """Run npm audit and pip-audit checks."""
    audit_results: Dict[str, Any] = {"python": [], "node": []}

    # Python pip-audit: check if pip-audit is installed first
    pip_audit_installed = False
    try:
        check = subprocess.run([sys.executable, "-c", "import pip_audit"], capture_output=True, timeout=3)
        pip_audit_installed = check.returncode == 0
    except Exception:
        pip_audit_installed = False

    if pip_audit_installed:
        req_files = ["requirements.txt"]
        if (project_root / "requirements-build.txt").exists():
            req_files.append("requirements-build.txt")

        for req_f in req_files:
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pip_audit", "-r", req_f, "--format=json"],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if proc.stdout:
                    # Strip any prefix warnings before the JSON block
                    stdout = proc.stdout
                    idx = stdout.find("{")
                    if idx != -1:
                        stdout = stdout[idx:]
                    data = json.loads(stdout)
                    dependencies = data.get("dependencies", [])
                    for dep in dependencies:
                        vulns = dep.get("vulns", [])
                        for v in vulns:
                            audit_results["python"].append(
                                {
                                    "package": dep.get("name"),
                                    "installed": dep.get("version"),
                                    "id": v.get("id"),
                                    "description": v.get("description", "")[:100],
                                    "fix_versions": ", ".join(v.get("fix_versions", [])),
                                }
                            )
            except Exception:
                pass
    else:
        audit_results["python_note"] = "pip-audit not installed in virtual environment (run: pip install pip-audit)."

    # Node npm audit
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        proc = subprocess.run(
            f"{npm_cmd} audit --json", cwd=str(project_root), capture_output=True, text=True, timeout=20, shell=True
        )
        if proc.stdout:
            try:
                data = json.loads(proc.stdout)
                vulnerabilities = data.get("vulnerabilities", {})
                for name, details in vulnerabilities.items():
                    severity = details.get("severity", "unknown")
                    via = details.get("via", [])
                    title = via[0].get("title", "") if via and isinstance(via[0], dict) else ""
                    audit_results["node"].append({"package": name, "severity": severity, "title": title})
            except Exception:
                pass
    except Exception:
        pass

    return audit_results


def generate_report(project_root: Path) -> str:
    """Generate Markdown report for frontend, backend, and build dependencies."""
    py_deps = check_python_dependencies(project_root, "requirements.txt")
    build_deps = (
        check_python_dependencies(project_root, "requirements-build.txt")
        if (project_root / "requirements-build.txt").exists()
        else []
    )
    node_deps = check_node_dependencies(project_root)
    audits = run_security_audits(project_root)

    outdated_py = [p for p in py_deps if p["bump"] in ("Major", "Minor", "Patch")]
    outdated_build = [b for b in build_deps if b["bump"] in ("Major", "Minor", "Patch")]
    outdated_node = [n for n in node_deps if n["bump"] in ("Major", "Minor", "Patch")]

    lines = []
    lines.append("# 📦 Dependency Health & Upgrade Report\n")
    lines.append(f"**Target Workspace:** `{project_root.name}`\n")

    # Overview Metrics
    lines.append("## Overview Summary")
    lines.append(f"- **Backend (Runtime Python) Outdated:** {len(outdated_py)} / {len(py_deps)} packages")
    if build_deps:
        lines.append(f"- **Build (Desktop EXE Python) Outdated:** {len(outdated_build)} / {len(build_deps)} packages")
    lines.append(f"- **Frontend (Node/Playwright) Outdated:** {len(outdated_node)} / {max(len(node_deps), 2)} packages")
    lines.append(
        f"- **Security Vulnerabilities:** {len(audits.get('python', []))} Python, {len(audits.get('node', []))} Node\n"
    )

    # Backend Table
    lines.append("## 🐍 Backend Runtime Dependencies (`requirements.txt`)")
    if not outdated_py:
        lines.append("All runtime Python dependencies match latest available versions! 🟢\n")
    else:
        lines.append("| Package | Defined in Req | Installed | Latest PyPI | Bump Type | Risk Level |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for p in py_deps:
            if p["bump"] in ("Major", "Minor", "Patch"):
                lines.append(
                    f"| **{p['package']}** | `{p['defined']}` | `{p['installed']}` | "
                    f"`{p['latest']}` | {p['bump']} | {p['risk']} |"
                )
        lines.append("")

    # Build Dependencies Table
    if build_deps:
        lines.append("## 🔨 Desktop Build Dependencies (`requirements-build.txt`)")
        if not outdated_build:
            lines.append("All desktop packaging dependencies match latest available versions! 🟢\n")
        else:
            lines.append("| Package | Defined in Req | Installed in venv | Latest PyPI | Bump Type | Risk Level |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for b in build_deps:
                inst_str = b["installed"] if b.get("is_installed") else f"Not installed (`{b['installed']}`)"
                lines.append(
                    f"| **{b['package']}** | `{b['defined']}` | {inst_str} | "
                    f"`{b['latest']}` | {b['bump']} | {b['risk']} |"
                )
            lines.append("")

    # Frontend Table
    lines.append("## 🌐 Frontend & Tooling Dependencies (`package.json`)")
    if not outdated_node:
        lines.append("All Node / Playwright dependencies are up to date! 🟢\n")
    else:
        lines.append("| Package | Current | Wanted (SemVer) | Latest npm | Bump Type | Risk Level |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for n in node_deps:
            lines.append(
                f"| **{n['package']}** | `{n['current']}` | `{n['wanted']}` | "
                f"`{n['latest']}` | {n['bump']} | {n['risk']} |"
            )
        lines.append("")

    # Security Advisories
    lines.append("## 🛡️ Security Vulnerabilities & Advisories")
    py_vulns = audits.get("python", [])
    node_vulns = audits.get("node", [])
    py_note = audits.get("python_note")

    if not py_vulns and not node_vulns:
        if py_note:
            lines.append(f"No known vulnerabilities reported. *(Note: {py_note})*\n")
        else:
            lines.append("No known vulnerabilities detected across Python or Node dependencies. 🛡️\n")
    else:
        if py_vulns:
            lines.append("### Python (pip-audit)")
            for v in py_vulns:
                lines.append(
                    f"- **{v['package']}** ({v['installed']}): {v['id']} - "
                    f"{v['description']} (Fix: {v['fix_versions']})"
                )
        if py_note:
            lines.append(f"*(Note: {py_note})*")
        if node_vulns:
            lines.append("### Node (npm audit)")
            for nv in node_vulns:
                lines.append(f"- **{nv['package']}** [Severity: {nv['severity'].upper()}]: {nv['title']}")
        lines.append("")

    # Upgrade Suggestions
    lines.append("## 💡 Upgrade Strategy & Suggestions\n")

    patch_minor = [p for p in outdated_py + outdated_node if p["bump"] in ("Minor", "Patch")]
    major_bumps = [p for p in outdated_py + outdated_node if p["bump"] == "Major"]

    if patch_minor:
        lines.append("### Step 1: Recommended Safe Updates (Patch / Minor)")
        lines.append("These updates provide bugfixes and feature enhancements with low risk of breaking changes:")
        for item in patch_minor:
            curr = item.get("installed") or item.get("current")
            lines.append(f"- ` {item['package']} `: {curr} ➜ **{item['latest']}** ({item['bump']})")
        lines.append("")

    if major_bumps:
        lines.append("### Step 2: Major Version Updates (Evaluate Carefully)")
        lines.append("These upgrades may introduce breaking changes or require code updates:")
        for item in major_bumps:
            curr = item.get("installed") or item.get("current")
            lines.append(f"- ` {item['package']} `: {curr} ➜ **{item['latest']}** ({item['risk']})")
        lines.append("")

    lines.append("### Step 3: Verification After Updates")
    lines.append("Always run the full test and lint suite after applying updates:")
    lines.append("```powershell")
    lines.append("ruff check src")
    lines.append("ruff format src")
    lines.append("mypy src")
    lines.append("pytest -v")
    lines.append("npx playwright test")
    lines.append("```")

    return "\n".join(lines)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[4]
    if not (root / "requirements.txt").exists():
        root = Path.cwd()
    print(generate_report(root))
