const { QueueHeads } = require("./QueueHeads.cjs");

async function CancelStale(Github, Context, RunInfo) {
  if (
    RunInfo.event !== "merge_group" ||
    RunInfo.path !== ".github/workflows/MergeQueue.yml" ||
    RunInfo.repository?.id !== Context.payload.repository.id ||
    RunInfo.head_repository?.id !== Context.payload.repository.id ||
    !RunInfo.head_branch?.startsWith("gh-readonly-queue/main/") ||
    !/^[0-9a-f]{40}$/.test(RunInfo.head_sha) ||
    !["queued", "in_progress", "waiting", "pending", "requested"].includes(
      RunInfo.status,
    )
  )
    return false;
  const Heads = await QueueHeads(Github, Context.repo);
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
  await Github.rest.actions.cancelWorkflowRun({
    ...Context.repo,
    run_id: RunInfo.id,
  });
  return true;
}

module.exports = { CancelStale };
