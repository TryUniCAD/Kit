async function CheckQueueIdle(Github, RepoInfo) {
  const Result = await Github.graphql(
    `query($owner:String!, $repo:String!) {
      repository(owner:$owner, name:$repo) {
        mergeQueue(branch:"main") { entries(first:1) { totalCount } }
      }
    }`,
    RepoInfo,
  );
  const Count = Result.repository?.mergeQueue?.entries?.totalCount;
  if (!Number.isInteger(Count) || Count < 0)
    throw new Error("Queue admission requires current queue metadata");
  if (Count > 0) return false;
  for (const Status of [
    "queued",
    "in_progress",
    "waiting",
    "pending",
    "requested",
  ]) {
    const RunList = await Github.paginate(
      Github.rest.actions.listWorkflowRuns,
      {
        ...RepoInfo,
        workflow_id: "MergeQueue.yml",
        event: "merge_group",
        status: Status,
        per_page: 100,
      },
    );
    if (RunList.length) return false;
  }
  return true;
}

module.exports = { CheckQueueIdle };
