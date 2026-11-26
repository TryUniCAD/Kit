set -euo pipefail
ArtifactName="${1:?}"
OutputRoot="${2:?}"
if ! RunId="$(
  gh api "repos/${GITHUB_REPOSITORY}/actions/artifacts?name=${ArtifactName}&per_page=100" --jq '
    [.artifacts[]
      | select(.expired | not)
      | select((.workflow_run.head_branch // "") | startswith("gh-readonly-queue/"))
      | select(.workflow_run.head_repository_id == .workflow_run.repository_id)]
    | sort_by(.created_at) | reverse | .[].workflow_run.id'
)"; then
  echo "::warning::Duration history lookup failed for ${ArtifactName}; every test remains scheduled with fallback weights"
  exit 0
fi
while IFS= read -r CandidateId; do
  test -n "$CandidateId" || break
  if ! Source="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${CandidateId}" --jq '"\(.event) \(.path)"')"; then
    echo "::warning::Duration history provenance lookup failed; using fallback weights"
    exit 0
  fi
  if [ "$Source" = 'merge_group .github/workflows/MergeQueue.yml' ]; then
    DownloadRoot="$(mktemp -d)"
    if ! gh run download "$CandidateId" --repo "$GITHUB_REPOSITORY" --name "$ArtifactName" --dir "$DownloadRoot"; then
      echo "::warning::Duration history download failed; incomplete history will not be used"
      exit 0
    fi
    mkdir -p "$(dirname "$OutputRoot")"
    mv "$DownloadRoot" "$OutputRoot"
    exit 0
  fi
done <<< "$RunId"
echo "No trusted duration history for ${ArtifactName}; use deterministic fallback weights" >> "$GITHUB_STEP_SUMMARY"
