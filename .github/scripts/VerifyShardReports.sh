set -euo pipefail
ReportRoot="${1:?}"
ReportPrefix="${2:?}"
RunAttempt="${3:?}"
NativePattern="${4:-}"
Collected=""
SelectedFiles=()
ReportFiles=()
for ShardIndex in 1 2 3 4; do
  ArtifactAttempt="$RunAttempt"
  while [ "$ArtifactAttempt" -gt 0 ]; do
    ReportDir="$ReportRoot/$ReportPrefix-shard-$ShardIndex-$ArtifactAttempt"
    if [ -d "$ReportDir" ]; then
      break
    fi
    ArtifactAttempt=$((ArtifactAttempt - 1))
  done
  test "$ArtifactAttempt" -gt 0
  if [ -z "$Collected" ]; then
    Collected="$ReportDir/Collected.txt"
    test -s "$Collected"
  fi
  cmp "$Collected" "$ReportDir/Collected.txt"
  SelectedFiles+=("$ReportDir/Selected.txt")
  ReportFiles+=("$ReportDir/Report.jsonl")
  test -s "$ReportDir/Selected.txt"
  jq --slurp --exit-status --rawfile Selected "$ReportDir/Selected.txt" '
    ($Selected | split("\n") | map(select(length > 0)) | sort) as $Expected
    | ([.[] | select(.["$report_type"] == "SessionFinish")] | length) == 1
      and all(.[]; .["$report_type"] != "SessionFinish" or .exitstatus == 0)
      and all(.[]; .outcome != "failed")
      and ([.[] | select(.["$report_type"] == "TestReport")
            | select(.when == "call" or (.when == "setup" and .outcome == "skipped"))
            | .nodeid] | sort) == $Expected
    ' "$ReportDir/Report.jsonl"
done
cat "${SelectedFiles[@]}" | LC_ALL=C sort > "$ReportRoot/Executed.txt"
cmp "$Collected" "$ReportRoot/Executed.txt"
if [ -n "$NativePattern" ]; then
  jq --slurp --exit-status --arg NativePattern "$NativePattern" '
    any(.[]; .["$report_type"] == "TestReport" and .when == "call"
      and .outcome == "passed" and (.nodeid | test($NativePattern)))
    ' "${ReportFiles[@]}"
fi
echo "Every collected case ran exactly once across four successful shards" >> "$GITHUB_STEP_SUMMARY"
