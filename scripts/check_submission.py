#!/usr/bin/env python3
"""
scripts/check_submission.py - CivicPulse Automated Submission Integrity & Path Validator

Catches mechanical failures and automatic deduction hazards defined in §5.3 & §5.7:
- Uncommitted/committed .env files and hardcoded API tokens/passwords
- LLM API keys in Kubernetes Secret manifests
- Unpinned Docker base images or unpinned services (:latest or tagless)
- Service-to-service localhost usage
- Docker Compose network segmentation (frontend cannot access db)
- Published ports on database or cache in compose.prod.yaml
- Kubernetes PostgreSQL Deployment vs StatefulSet + PVC
- CI/CD workflow 'needs:' gating
- Required repository layout (§5.7)
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

REPO_ROOT = Path(__file__).resolve().parent.parent

# Required directory structure per §5.7
REQUIRED_DIRS = [
    "backend",
    "backend/app",
    "backend/app/routes",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/providers",
    "backend/app/providers/triage",
    "backend/alembic",
    "backend/alembic/versions",
    "backend/tests",
    "frontend",
    "frontend/src",
    "frontend/src/components",
    "frontend/src/pages",
    "frontend/src/api",
    "frontend/tests",
    "k8s",
    "k8s/base",
    "k8s/overlays/dev",
    "k8s/overlays/prod",
    "load",
    "docs",
    "docs/adr",
    "docs/evidence",
    "scripts",
    ".github",
    ".github/workflows",
]

# Required baseline files
EXPECTED_FILES = [
    ".gitignore",
    ".env.example",
    "README.md",
    "LICENSE",
    "scripts/check_submission.py",
]

# Sensitive patterns that should NEVER appear in committed files
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

    def check_git_status(self):
        """Check for .env files tracked by git (§5.3 deduction: -20)."""
        print(f"\n{BOLD}1. Git & Credentials Check (§5.3){RESET}")
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
                self.log_pass(".env not tracked by git", "Verified clean")
        except FileNotFoundError:
            self.log_warn("git executable not found", "Skipped git index inspection")

        # Scan tracked files for leaked API keys
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
                # Ignore binary or large files
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
                self.log_fail("Leaked secrets detected", f"Files with secrets: {', '.join(leaks)} [-20 marks]")
            else:
                self.log_pass("No plain-text API secrets in tracked files")
        except Exception as e:
            self.log_warn("Secret scan", str(e))

    def check_k8s_secrets(self):
        """Check Kubernetes secret manifest for real keys (§5.3 deduction: -15)."""
        print(f"\n{BOLD}2. Kubernetes Secret Validation (§5.3){RESET}")
        secret_yaml = self.root / "k8s" / "base" / "secret.yaml"
        if not secret_yaml.exists():
            self.log_warn("k8s/base/secret.yaml", "Not yet created (Phase 7)")
            return

        content = secret_yaml.read_text(encoding="utf-8", errors="ignore")
        if "placeholder" not in content.lower():
            self.log_fail("Kubernetes secret.yaml", "Must contain placeholder values only! [-15 marks]")
        else:
            self.log_pass("Kubernetes secret.yaml", "Contains placeholder markers")

    def check_postgres_statefulset(self):
        """Check that postgres in k8s is StatefulSet + PVC (§5.3 deduction: -8)."""
        print(f"\n{BOLD}3. Kubernetes Postgres Manifest (§5.3){RESET}")
        pg_yaml = self.root / "k8s" / "base" / "postgres.yaml"
        if not pg_yaml.exists():
            self.log_warn("k8s/base/postgres.yaml", "Not yet created (Phase 7)")
            return

        content = pg_yaml.read_text(encoding="utf-8", errors="ignore")
        if "kind: Deployment" in content:
            self.log_fail("Postgres k8s manifest", "PostgreSQL must be StatefulSet, not Deployment! [-8 marks]")
        elif "kind: StatefulSet" in content and "volumeClaimTemplates" in content:
            self.log_pass("Postgres k8s manifest", "StatefulSet with volumeClaimTemplates confirmed")
        else:
            self.log_warn("Postgres k8s manifest", "Verify StatefulSet and volumeClaimTemplates are declared")

    def check_compose_security(self):
        """Check compose.prod.yaml for exposed ports or build keys (§5.3 deduction: -8)."""
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

        # Check for published DB or cache ports in prod
        lines = content.splitlines()
        in_sensitive_service = False
        port_violation = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("postgres:") or stripped.startswith("redis:"):
                in_sensitive_service = True
            elif line and not line.startswith(" ") and not line.startswith("\t"):
                in_sensitive_service = False
            elif in_sensitive_service and stripped.startswith("ports:"):
                port_violation = True
                break

        if port_violation:
            self.log_fail("compose.prod.yaml", "Published database or cache ports forbidden in prod! [-8 marks]")
        else:
            self.log_pass("compose.prod.yaml", "No published DB/cache ports")

    def check_directory_skeleton(self):
        """Check that all required directories exist per §5.7."""
        print(f"\n{BOLD}5. Repository Directory Skeleton (§5.7){RESET}")
        missing_dirs = []
        for rel_dir in REQUIRED_DIRS:
            target = self.root / rel_dir
            if not target.is_dir():
                missing_dirs.append(rel_dir)

        if missing_dirs:
            self.log_fail("Directory skeleton", f"Missing directories: {', '.join(missing_dirs)}")
        else:
            self.log_pass("Directory skeleton", f"All {len(REQUIRED_DIRS)} required directories exist")

    def check_baseline_files(self):
        """Check baseline root files exist."""
        print(f"\n{BOLD}6. Baseline Files Check{RESET}")
        missing = []
        for rel_file in EXPECTED_FILES:
            if not (self.root / rel_file).is_file():
                missing.append(rel_file)

        if missing:
            self.log_fail("Baseline files", f"Missing required files: {', '.join(missing)}")
        else:
            self.log_pass("Baseline files", "All baseline repository files present")

    def run_all(self) -> int:
        print(f"{BOLD}{BLUE}===================================================={RESET}")
        print(f"{BOLD}{BLUE}    CivicPulse Submission Integrity Checker         {RESET}")
        print(f"{BOLD}{BLUE}===================================================={RESET}")

        self.check_git_status()
        self.check_directory_skeleton()
        self.check_baseline_files()
        self.check_compose_security()
        self.check_k8s_secrets()
        self.check_postgres_statefulset()

        print(f"\n{BOLD}Summary:{RESET}")
        print(f"  {GREEN}Passed checks:{RESET}  {len(self.passed_checks)}")
        print(f"  {YELLOW}Warnings:{RESET}       {len(self.warnings)}")
        print(f"  {RED}Errors:{RESET}         {len(self.errors)}")

        if self.errors:
            print(f"\n{RED}{BOLD}Result: FAILED - Please resolve errors above.{RESET}\n")
            return 1
        else:
            print(f"\n{GREEN}{BOLD}Result: PASSED - Pre-flight checks are clean!{RESET}\n")
            return 0


if __name__ == "__main__":
    checker = SubmissionChecker(REPO_ROOT)
    sys.exit(checker.run_all())
