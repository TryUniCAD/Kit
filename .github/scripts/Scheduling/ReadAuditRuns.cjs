async function ReadAuditRuns(Github, RepoInfo) {
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
        status: Status,
        per_page: 100,
      },
    );
    if (
      RunList.some((RunInfo) =>
        ["workflow_dispatch", "push"].includes(RunInfo.event),
      )
    )
      return true;
  }
  return false;
}

module.exports = { ReadAuditRuns };
