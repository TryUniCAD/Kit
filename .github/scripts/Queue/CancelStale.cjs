async function CancelStale(Github, Context, RunInfo, Heads) {
  const BranchMatch =
    /^gh-readonly-queue\/main\/pr-([1-9][0-9]*)-[0-9a-f]{40}$/.exec(
      RunInfo.head_branch ?? "",
    );
  if (
    RunInfo.event !== "merge_group" ||
    ![
      ".github/workflows/MergeQueue.yml",
      ".github/workflows/WorkflowQuality.yml",
    ].includes(RunInfo.path) ||
    RunInfo.repository?.id !== Context.payload.repository.id ||
    RunInfo.head_repository?.id !== Context.payload.repository.id ||
    !BranchMatch ||
    !/^[0-9a-f]{40}$/.test(RunInfo.head_sha) ||
    !["queued", "in_progress", "waiting", "pending", "requested"].includes(
      RunInfo.status,
    )
  )
    return false;
  if (Heads.has(RunInfo.head_sha)) return false;
  try {
    await Github.rest.git.getRef({
      ...Context.repo,
      ref: `heads/${RunInfo.head_branch}`,
    });
    return false;
  } catch (ErrorInfo) {
    if (ErrorInfo.status !== 404) throw ErrorInfo;
  }
  const Result = await Github.graphql(
    `query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) { mergeQueueEntry { headCommit { oid } } }
      }
    }`,
    { ...Context.repo, number: Number(BranchMatch[1]) },
  );
  const PullInfo = Result.repository?.pullRequest;
  if (!PullInfo || !("mergeQueueEntry" in PullInfo))
    throw new Error("Current queue entry evidence unavailable");
  const EntryInfo = PullInfo.mergeQueueEntry;
  if (
    EntryInfo !== null &&
    (!/^[0-9a-f]{40}$/.test(EntryInfo.headCommit?.oid ?? "") ||
      EntryInfo.headCommit.oid === RunInfo.head_sha)
  )
    return false;
  await Github.rest.actions.cancelWorkflowRun({
    ...Context.repo,
    run_id: RunInfo.id,
  });
  return true;
}

module.exports = { CancelStale };
