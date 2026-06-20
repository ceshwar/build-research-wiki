#!/usr/bin/env bash
# Create GitHub issues for the SCUBA Ideaverse roadmap.
# Requires: gh auth login (once per machine)
#
# Usage:
#   ./scripts/create-roadmap-issues.sh
#   ./scripts/create-roadmap-issues.sh owner/repo
#
# Safe to re-run: skips issues whose title already exists (open or closed).

set -euo pipefail

REPO="${1:-ceshwar/build-research-wiki}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISSUES_DIR="${SCRIPT_DIR}/roadmap-issues"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

ensure_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  if ! gh label list --repo "$REPO" --search "$name" --json name -q '.[].name' 2>/dev/null | grep -qx "$name"; then
    gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null || true
  fi
}

issue_exists() {
  local title="$1"
  gh issue list --repo "$REPO" --state all --search "in:title \"${title}\"" --json title -q '.[].title' 2>/dev/null \
    | grep -Fxq "$title"
}

create_issue() {
  local title="$1"
  local labels="$2"
  local body_file="$3"

  if issue_exists "$title"; then
    echo "↷ Skipping (exists): $title"
    return 0
  fi

  if [[ ! -f "$body_file" ]]; then
    echo "Missing body file: $body_file" >&2
    return 1
  fi

  gh issue create --repo "$REPO" --title "$title" --label "$labels" --body-file "$body_file"
}

ensure_label "phase-2" "1B2A4A" "Near-term chart pipeline"
ensure_label "phase-3" "EA580C" "Full ingest for non-portfolio docks"
ensure_label "phase-4" "0E7490" "Discovery and synthesis"
ensure_label "phase-5" "64748B" "Product and team polish"
ensure_label "v0.4" "22C55E" "Shipped in v0.4 Ideaverse UI"
ensure_label "shipped" "86EFAC" "Completed and documented"

echo "Creating roadmap issues on $REPO …"

create_issue "v0.4 Ideaverse control panel — shipped" "v0.4,shipped" \
  "${ISSUES_DIR}/00-v04-shipped.md"

create_issue "Phase 2: LLM Deep Dive for portfolio PDFs" "enhancement,phase-2" \
  "${ISSUES_DIR}/01-llm-deep-dive.md"

create_issue "Phase 2: Theme and one-liner assistance" "enhancement,phase-2" \
  "${ISSUES_DIR}/02-theme-one-liner.md"

create_issue "Phase 2: Dive Computer per-paper Enrich actions" "enhancement,phase-2" \
  "${ISSUES_DIR}/03-enrich-actions.md"

create_issue "Phase 2: Entity and concept propagation on Deep Dive" "enhancement,phase-2" \
  "${ISSUES_DIR}/04-entity-propagation.md"

create_issue "Phase 3: Full LLM ingest — Literature Review dock" "enhancement,phase-3" \
  "${ISSUES_DIR}/05-lit-review-ingest.md"

create_issue "Phase 3: Full LLM ingest — Dive Log dock" "enhancement,phase-3" \
  "${ISSUES_DIR}/06-dive-log-ingest.md"

create_issue "Phase 3: Full LLM ingest — Ideas and Notes dock" "enhancement,phase-3" \
  "${ISSUES_DIR}/07-ideas-ingest.md"

create_issue "Phase 4: Sonar ping — related work discovery" "enhancement,phase-4" \
  "${ISSUES_DIR}/08-sonar-ping.md"

create_issue "Phase 4: Query to file — syntheses in the UI" "enhancement,phase-4" \
  "${ISSUES_DIR}/09-query-to-file.md"

create_issue "Phase 4: Auto-maintain cross-cutting threads in overview.md" "enhancement,phase-4" \
  "${ISSUES_DIR}/10-overview-threads.md"

create_issue "Phase 5: Reef profiles — custom chart shapes" "enhancement,phase-5" \
  "${ISSUES_DIR}/11-reef-profiles.md"

create_issue "Phase 5: Obsidian Dataview integration for Dive Computer stats" "enhancement,phase-5" \
  "${ISSUES_DIR}/12-dataview-stats.md"

echo ""
echo "Done. Roadmap issues:"
gh issue list --repo "$REPO" --search "Phase in:title" --limit 20
