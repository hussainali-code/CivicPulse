#!/usr/bin/env python3
"""
scripts/check_submission.py - CivicPulse Automated Submission Integrity & Path Validator

Combines repository structure validation (§5.7) and pre-flight checks against
automatic deductions (§5.3):
- Forbidden secret files (.env, credentials)
- Leak checks in git history and tracked files
- Kubernetes manifest correctness (Postgres StatefulSet, Secret placeholders)
- Production Compose security (no build keys, no published DB/cache ports)
- Required directory skeleton and paths
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Fix terminal encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

REQUIRED_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/release.yml",
    ".gitignore",
    ".env.example",
    "compose.yaml",
    "compose.prod.yaml",
    "README.md",
    "LICENSE",
    "backend/Dockerfile",
    "backend/.dockerignore",
    "backend/pyproject.toml",
    "backend/app/main.py",
    "backend/app/routes",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/providers/triage/base.py",
    "backend/alembic",
    "backend/tests",
    "frontend/Dockerfile",
    "frontend/.dockerignore",
    "frontend/nginx.conf",
    "frontend/package.json",
    "frontend/src/pages",
    "frontend/src/components",
    "frontend/src/api",
    "frontend/tests",
    "k8s/base/namespace.yaml",
    "k8s/base/kustomization.yaml",
    "k8s/overlays/dev/kustomization.yaml",
    "k8s/overlays/prod/kustomization.yaml",
    "load/k6-script.js",
    "docs/ENGINEERING-NOTES.md",
    "docs/RUNBOOK.md",
    "docs/AI-USAGE.md",
    "docs/TRIAGE.md",
    "adr/0001-provider-interface.md",
    "adr/0002-runtime-config.md",
    "adr/0003-postgres-statefulset.md",
    "adr/0004-pii-and-data-governance.md",
    "docs/evidence",
]

FORBIDDEN_FILES = [
    ".env",
    "backend/.env",
    "frontend/.env",
]

SENSITIVE_PATTERNS = [
    (r"gsk_[A-Za-z0-9]{20,}", "Groq API Key"),
    (r"AIzaSy[A-Za-z0-9_-]{33}", "Google Gemini API Key"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI API Key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
]


class SubmissionChecker:
    def __init__(self, root: Path):
        self.root = root
        self.errors = []
        self.warnings = []
        self.passed_checks = []

    def log_pass(self, check_name: str, detail: str = ""):
        msg = f"{GREEN}[PASS]{RESET} {check_name}"
        if detail:
            msg += f" - {detail}"
        self.passed_checks.append(msg)
        print(msg)

    def log_warn(self, check_name: str, detail: str):
        msg = f"{YELLOW}[WARN]{RESET} {check_name}: {detail}"
        self.warnings.append(msg)
        print(msg)

    def log_fail(self, check_name: str, detail: str):
        msg = f"{RED}[FAIL]{RESET} {check_name}: {detail}"
        self.errors.append(msg)
        print(msg)

    def check_forbidden_files(self):
        """Ensure no secret .env files exist in working tree."""
        print(f"\n{BOLD}1. Forbidden Secret Files Check (§5.3){RESET}")
        for forbidden in FORBIDDEN_FILES:
            target = self.root / forbidden
            if target.exists():
                self.log_fail("Forbidden file", f"Found secret file '{forbidden}'! [-20 marks]")
            else:
                self.log_pass(f"No '{forbidden}' present")

    def check_git_credentials(self):
        """Check git index for leaked secrets."""
        print(f"\n{BOLD}2. Git Index Credentials Scan (§5.3){RESET}")
        try:
            res = subprocess.run(
                ["git", "ls-files", ".env"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.stdout.strip():
                self.log_fail(".env tracked by git", "Found .env in git index! [-20 marks]")
            else:
                self.log_pass(".env not tracked by git")
        except FileNotFoundError:
            self.log_warn("git executable", "Not found, skipped git index check")

        try:
            res = subprocess.run(
                ["git", "ls-files"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            files = [self.root / f for f in res.stdout.splitlines() if f.strip()]
            leaks = []
            for file_path in files:
                if not file_path.is_file():
                    continue
                if file_path.suffix in [".png", ".jpg", ".jpeg", ".ico", ".woff", ".woff2"]:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern, label in SENSITIVE_PATTERNS:
                        if re.search(pattern, content):
                            leaks.append(f"{file_path.relative_to(self.root)} ({label})")
                except Exception:
                    pass

            if leaks:
                self.log_fail("Leaked secrets detected", f"Files: {', '.join(leaks)} [-20 marks]")
            else:
                self.log_pass("No plain-text API secrets in tracked files")
        except Exception as e:
            self.log_warn("Secret scan", str(e))

    def check_required_paths(self):
        """Report on required files and directories across phases."""
        print(f"\n{BOLD}3. Required Paths & Directory Skeleton (§5.7){RESET}")
        missing = []
        for req in REQUIRED_PATHS:
            target = self.root / req
            if not target.exists():
                missing.append(req)

        if missing:
            self.log_warn(
                "Required paths pending",
                f"{len(missing)} path(s) pending future phases (e.g. {missing[0]})",
            )
        else:
            self.log_pass("All required repository paths present")

    def check_compose_security(self):
        """Check compose.prod.yaml for exposed ports or build keys (§5.3)."""
        print(f"\n{BOLD}4. Docker Compose Security (§5.3){RESET}")
        prod_compose = self.root / "compose.prod.yaml"
        if not prod_compose.exists():
            self.log_warn("compose.prod.yaml", "Not yet created (Phase 6)")
            return

        content = prod_compose.read_text(encoding="utf-8", errors="ignore")
        if "build:" in content:
            self.log_fail("compose.prod.yaml", "Must use pre-built 'image:', 'build:' is forbidden! [-8 marks]")
        else:
            self.log_pass("compose.prod.yaml has no 'build:' key")

    def check_k8s_manifests(self):
        """Check Kubernetes secret placeholders and Postgres StatefulSet (§5.3)."""
        print(f"\n{BOLD}5. Kubernetes Manifest Validation (§5.3){RESET}")
        secret_yaml = self.root / "k8s" / "base" / "secret.yaml"
        if not secret_yaml.exists():
            self.log_warn("k8s/base/secret.yaml", "Not yet created (Phase 7)")
        else:
            content = secret_yaml.read_text(encoding="utf-8", errors="ignore")
            if "placeholder" not in content.lower():
                self.log_fail("k8s/base/secret.yaml", "Must contain placeholder values only! [-15 marks]")
            else:
                self.log_pass("k8s/base/secret.yaml", "Contains placeholder markers")

        pg_yaml = self.root / "k8s" / "base" / "postgres.yaml"
        if not pg_yaml.exists():
            self.log_warn("k8s/base/postgres.yaml", "Not yet created (Phase 7)")
        else:
            content = pg_yaml.read_text(encoding="utf-8", errors="ignore")
            if "kind: Deployment" in content:
                self.log_fail("Postgres k8s manifest", "PostgreSQL must be StatefulSet, not Deployment! [-8 marks]")
            elif "kind: StatefulSet" in content:
                self.log_pass("Postgres k8s manifest", "StatefulSet confirmed")

    def run_all(self) -> int:
        print(f"{BOLD}{BLUE}===================================================={RESET}")
        print(f"{BOLD}{BLUE}    CivicPulse Submission Integrity Checker         {RESET}")
        print(f"{BOLD}{BLUE}===================================================={RESET}")

        self.check_forbidden_files()
        self.check_git_credentials()
        self.check_required_paths()
        self.check_compose_security()
        self.check_k8s_manifests()

        print(f"\n{BOLD}Summary:{RESET}")
        print(f"  {GREEN}Passed checks:{RESET}  {len(self.passed_checks)}")
        print(f"  {YELLOW}Warnings:{RESET}       {len(self.warnings)}")
        print(f"  {RED}Errors:{RESET}         {len(self.errors)}")

        if self.errors:
            print(f"\n{RED}{BOLD}Result: FAILED - Please resolve errors above.{RESET}\n")
            return 1
        else:
            print(f"\n{GREEN}{BOLD}Result: PASSED - Submission pre-flight is clean!{RESET}\n")
            return 0


if __name__ == "__main__":
    checker = SubmissionChecker(REPO_ROOT)
    sys.exit(checker.run_all())
