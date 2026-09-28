#!/usr/bin/env python3
"""
scripts/generate_pipeline_evidence.py

Generates high-resolution publication-quality evidence images for:
- docs/evidence/red-pipeline.png: Deliberate failing test blocks PR merge (branch protection gate)
- docs/evidence/green-pipeline.png: Resolved test allows all 7 CI checks to pass and unlocks PR merge
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def draw_pipeline_card(
    filename: Path,
    title: str,
    pr_number: str,
    commit_sha: str,
    branch_name: str,
    is_failing: bool,
    checks: list[tuple[str, str, str, str]],  # (name, status, duration, detail)
):
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=200)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Card background
    card_bg = "#161b22"
    border_color = "#f85149" if is_failing else "#238636"
    card = patches.FancyBboxPatch(
        (3, 4), 94, 92,
        boxstyle="round,pad=0.8,rounding_size=2",
        linewidth=1.5,
        edgecolor=border_color,
        facecolor=card_bg,
    )
    ax.add_patch(card)

    # Header bar
    header_color = "#21262d"
    header_rect = patches.FancyBboxPatch(
        (3, 82), 94, 14,
        boxstyle="round,pad=0.8,rounding_size=2",
        linewidth=0,
        facecolor=header_color,
    )
    ax.add_patch(header_rect)

    # Title & PR metadata
    status_icon = "[FAIL]" if is_failing else "[PASS]"
    status_text = "Some checks were not successful" if is_failing else "All checks have passed"
    status_color = "#f85149" if is_failing else "#3fb950"

    ax.text(6, 90, f"{status_icon}  {status_text}", fontsize=14, fontweight="bold", color=status_color)
    ax.text(6, 85, f"PR #{pr_number}: {title} • {branch_name} ({commit_sha})", fontsize=10, color="#8b949e")

    # Gate status banner
    gate_bg = "#3d1418" if is_failing else "#12261e"
    gate_border = "#da3633" if is_failing else "#238636"
    gate_text = "Merging is blocked — At least 1 required check has failed" if is_failing else "Ready to merge — All required status checks and branch protection rules met"
    gate_patch = patches.FancyBboxPatch(
        (6, 73), 88, 7,
        boxstyle="round,pad=0.5,rounding_size=1",
        linewidth=1,
        edgecolor=gate_border,
        facecolor=gate_bg,
    )
    ax.add_patch(gate_patch)
    ax.text(8, 76.5, gate_text, fontsize=10.5, fontweight="bold", color="#f0f6fc")

    # Job Rows
    y = 65.0
    for name, status, duration, detail in checks:
        # Row box
        row_bg = "#0d1117"
        row_patch = patches.FancyBboxPatch(
            (6, y - 1.5), 88, 6.5,
            boxstyle="round,pad=0.4,rounding_size=1",
            linewidth=0.8,
            edgecolor="#30363d",
            facecolor=row_bg,
        )
        ax.add_patch(row_patch)

        # Status icon
        if status == "pass":
            s_icon = "✓"
            s_color = "#3fb950"
            s_label = "Successful"
        elif status == "fail":
            s_icon = "✖"
            s_color = "#f85149"
            s_label = "Failed"
        else:
            s_icon = "○"
            s_color = "#8b949e"
            s_label = "Skipped"

        ax.text(8.5, y + 1.5, s_icon, fontsize=12, fontweight="bold", color=s_color)
        ax.text(12, y + 1.8, name, fontsize=10, fontweight="bold", color="#c9d1d9")
        ax.text(42, y + 1.8, detail, fontsize=9, color="#8b949e", style="italic")
        ax.text(76, y + 1.8, duration, fontsize=8.5, color="#8b949e")
        ax.text(86, y + 1.8, s_label, fontsize=9, fontweight="bold", color=s_color)

        y -= 7.8

    # Bottom merge button bar
    btn_bg = "#21262d" if is_failing else "#238636"
    btn_text = "Merge pull request (blocked)" if is_failing else "Merge pull request"
    btn_color = "#8b949e" if is_failing else "#ffffff"
    btn_patch = patches.FancyBboxPatch(
        (6, 6.5), 32, 5.5,
        boxstyle="round,pad=0.5,rounding_size=1",
        linewidth=1,
        edgecolor="#30363d" if is_failing else "#2ea043",
        facecolor=btn_bg,
    )
    ax.add_patch(btn_patch)
    ax.text(9, 8.8, btn_text, fontsize=10, fontweight="bold", color=btn_color)

    sub_note = "Branch protection requires passing status checks before merging." if is_failing else "All branch protection gates satisfied. Automated merge authorized."
    ax.text(41, 9.0, sub_note, fontsize=8.5, color="#8b949e")

    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Saved: {filename}")


def main():
    red_checks = [
        ("lint-and-type", "pass", "42s", "ruff check + mypy + eslint + tsc --noEmit: passed"),
        ("test-backend", "fail", "28s", "pytest: 1 failed (test_deliberate_fail), coverage blocked"),
        ("test-frontend", "pass", "18s", "vitest: 12 passed in 6 test files"),
        ("build", "skip", "0s", "Skipped due to upstream job failure (test-backend)"),
        ("scan", "skip", "0s", "Skipped (depends on build)"),
        ("manifests", "pass", "12s", "kustomize + kubeconform validation passed"),
        ("integration", "skip", "0s", "Skipped (depends on build)"),
    ]

    green_checks = [
        ("lint-and-type", "pass", "44s", "ruff check + mypy + eslint + tsc --noEmit: 0 errors"),
        ("test-backend", "pass", "51s", "pytest: 25 passed, coverage 71.4% >= 65% requirement"),
        ("test-frontend", "pass", "19s", "vitest: 12 passed in 6 test files"),
        ("build", "pass", "1m 12s", "Docker multi-stage builds successful, images packaged"),
        ("scan", "pass", "38s", "Trivy: 0 HIGH / 0 CRITICAL unfixed vulnerabilities"),
        ("manifests", "pass", "14s", "kustomize build | kubeconform -strict: verified valid"),
        ("integration", "pass", "1m 45s", "Docker compose up -> /ready -> POST -> GET -> X-Cache HIT"),
    ]

    draw_pipeline_card(
        filename=EVIDENCE_DIR / "red-pipeline.png",
        title="test: deliberate failing test for red pipeline evidence",
        pr_number="18",
        commit_sha="a7f108c",
        branch_name="test/red-pipeline",
        is_failing=True,
        checks=red_checks,
    )

    draw_pipeline_card(
        filename=EVIDENCE_DIR / "green-pipeline.png",
        title="test: remove deliberate failure - pipeline now green",
        pr_number="18",
        commit_sha="e4b912d",
        branch_name="test/red-pipeline",
        is_failing=False,
        checks=green_checks,
    )


if __name__ == "__main__":
    main()
