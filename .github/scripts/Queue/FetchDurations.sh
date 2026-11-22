set -euo pipefail
ArtifactName="${1:?}"
OutputRoot="${2:?}"
RunId="$(
  gh api "repos/${GITHUB_REPOSITORY}/actions/artifacts?name=${ArtifactName}&per_page=100" --jq '
    [.artifacts[]
      | select(.expired | not)
      | select((.workflow_run.head_branch // "") | startswith("gh-readonly-queue/"))
      | select(.workflow_run.head_repository_id == .workflow_run.repository_id)]
    | sort_by(.created_at) | reverse | .[].workflow_run.id'
)"
while IFS= read -r CandidateId; do
  test -n "$CandidateId" || break
  Source="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${CandidateId}" --jq '"\(.event) \(.path)"')"
  if [ "$Source" = 'merge_group .github/workflows/MergeQueue.yml' ]; then
    gh run download "$CandidateId" --repo "$GITHUB_REPOSITORY" --name "$ArtifactName" --dir "$OutputRoot"
    exit 0
  fi
done <<< "$RunId"
echo "No trusted duration history for ${ArtifactName}; use deterministic fallback weights" >> "$GITHUB_STEP_SUMMARY"
