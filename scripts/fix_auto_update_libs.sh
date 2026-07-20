#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/fix_auto_update_libs.sh [options]

Options:
  --inventory <path>      YAML inventory file (default: automation/auto_update_libs_targets.yaml)
  --repo <owner/name>     Process one repo only
  --branch-prefix <text>  Branch name prefix (default: fix/auto-update-libs-permissions)
  --dry-run               Do all local steps except push and PR creation
  -h, --help              Show this help
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

inventory="automation/auto_update_libs_targets.yaml"
repo_filter=""
branch_prefix="fix/auto-update-libs-permissions"
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --inventory)
      inventory="$2"
      shift 2
      ;;
    --repo)
      repo_filter="$2"
      shift 2
      ;;
    --branch-prefix)
      branch_prefix="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd git
require_cmd gh
require_cmd python3

if [[ ! -f "$inventory" ]]; then
  echo "Inventory file not found: $inventory" >&2
  exit 1
fi

extract_targets() {
  python3 - "$inventory" "$repo_filter" <<'PY'
import json
import sys
from pathlib import Path
import yaml

inventory_path = Path(sys.argv[1])
repo_filter = sys.argv[2]
data = yaml.safe_load(inventory_path.read_text())
repos = data.get("repos", [])

for repo in repos:
    if repo_filter and repo.get("name") != repo_filter:
        continue
    print(json.dumps({
        "name": repo["name"],
        "url": repo["url"],
        "workflow_path": repo["workflow_path"],
        "latest_run_url": repo.get("latest_run_url", ""),
        "failure_streak": repo.get("failure_streak", ""),
    }))
PY
}

targets="$(extract_targets)"
if [[ -z "$targets" ]]; then
  echo "No matching targets found."
  exit 1
fi

echo "Starting auto_update_libs permission fix run"
echo "Inventory: $inventory"
if [[ -n "$repo_filter" ]]; then
  echo "Filtered repo: $repo_filter"
fi
echo

while IFS= read -r target; do
  [[ -z "$target" ]] && continue

  name="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["name"])' "$target")"
  workflow_path="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["workflow_path"])' "$target")"
  latest_run_url="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("latest_run_url",""))' "$target")"
  failure_streak="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("failure_streak",""))' "$target")"
  repo_short="${name#*/}"
  branch="${branch_prefix}-${repo_short}"

  echo "=== Processing $name ==="
  tmpdir="$(mktemp -d)"

  gh repo clone "$name" "$tmpdir/repo" -- --quiet
  cd "$tmpdir/repo"

  if [[ ! -f "$workflow_path" ]]; then
    echo "Workflow file not found: $workflow_path"
    cd - >/dev/null
    rm -rf "$tmpdir"
    continue
  fi

  git checkout -b "$branch"

  set +e
  python3 - "$workflow_path" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

if "id-token: write" in text and "pull-requests: write" in text and "contents: write" in text:
    print("Permissions already present.")
    raise SystemExit(10)

needle = (
    "    uses: canonical/operator-workflows/.github/workflows/auto_update_charm_libs.yaml@main\n"
    "    secrets: inherit\n"
)
replacement = (
    "    uses: canonical/operator-workflows/.github/workflows/auto_update_charm_libs.yaml@main\n"
    "    permissions:\n"
    "      contents: write\n"
    "      pull-requests: write\n"
    "      id-token: write\n"
    "    secrets: inherit\n"
)

if needle not in text:
    raise SystemExit(f"Could not find expected workflow pattern in {path}")

path.write_text(text.replace(needle, replacement, 1))
print("Workflow permissions patch applied.")
PY
  patch_status=$?
  set -e
  if [[ $patch_status -eq 10 ]]; then
    echo "No change needed."
    cd - >/dev/null
    rm -rf "$tmpdir"
    continue
  elif [[ $patch_status -ne 0 ]]; then
    echo "Failed to patch $workflow_path in $name"
    cd - >/dev/null
    rm -rf "$tmpdir"
    continue
  fi

  grep -q "permissions:" "$workflow_path"
  grep -q "contents: write" "$workflow_path"
  grep -q "pull-requests: write" "$workflow_path"
  grep -q "id-token: write" "$workflow_path"
  python3 - <<'PY' "$workflow_path"
import sys
from pathlib import Path
import yaml
yaml.safe_load(Path(sys.argv[1]).read_text())
print("YAML parse check passed.")
PY

  git add "$workflow_path"
  git commit -m "fix(ci): grant reusable workflow write permissions"

  if [[ "$dry_run" -eq 1 ]]; then
    echo "Dry run: skipping push and PR creation for $name"
  else
    git push -u origin "$branch"
    gh pr create \
      --base main \
      --head "$branch" \
      --title "fix(ci): grant permissions for auto_update_libs reusable workflow" \
      --body "$(cat <<EOF
## Summary
- add explicit permissions to \`$workflow_path\`
- grant \`contents: write\`, \`pull-requests: write\`, and \`id-token: write\` to the reusable-workflow caller job

## Why
The auto-update libraries workflow has a long startup-failure streak (${failure_streak} runs).  
Latest failed run: ${latest_run_url}

This repository uses read-only default workflow token permissions, but the called reusable workflow requires write scopes.

## Resolution
Add explicit caller permissions so scheduled runs can start and create update PRs successfully.
EOF
)"
  fi

  cd - >/dev/null
  rm -rf "$tmpdir"
  echo "Completed $name"
  echo
done <<< "$targets"

echo "Done."
