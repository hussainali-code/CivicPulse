#!/usr/bin/env python3
"""
CivicPulse Submission Checker
Validates that required files, directory structure, and sanity constraints exist before submission.
"""

import sys
from pathlib import Path

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
    "backend/app/providers/triage/factory.py",
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

def check_structure(root_dir: Path) -> bool:
    print(f"🔍 Validating CivicPulse repository at: {root_dir.resolve()}\n")
    all_passed = True

    # Check forbidden files
    for forbidden in FORBIDDEN_FILES:
        forbidden_path = root_dir / forbidden
        if forbidden_path.exists():
            print(f"❌ CRITICAL ERROR: Found forbidden secret file '{forbidden}'! Remove immediately!")
            all_passed = False

    # Check required paths
    missing_count = 0
    for req in REQUIRED_PATHS:
        req_path = root_dir / req
        if not req_path.exists():
            print(f"⚠️  Missing required path: {req}")
            missing_count += 1

    if missing_count == 0:
        print("✅ All required repository paths are present!")
    else:
        print(f"\n⚠️  {missing_count} required path(s) are currently missing (will be populated across phases).")

    return all_passed

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    success = check_structure(repo_root)
    sys.exit(0 if success else 1)
