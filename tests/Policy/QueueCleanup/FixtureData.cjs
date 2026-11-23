function FixtureData(CaseName) {
  const Current = {
    id: 42,
    event: "merge_group",
    path: ".github/workflows/MergeQueue.yml",
    repository: { id: 1 },
    head_repository: { id: 1 },
    head_branch: `gh-readonly-queue/main/pr-42-${"b".repeat(40)}`,
    head_sha: "a".repeat(40),
    status: "in_progress",
  };
  const Changes = {
    completed: { status: "completed" },
    manual: { event: "workflow_dispatch" },
    pull: { event: "pull_request" },
    workflow: { path: ".github/workflows/Other.yml" },
    fork: { head_repository: { id: 2 } },
    repository: { repository: { id: 2 } },
    branch: { head_branch: "gh-readonly-queue/other/pr-42" },
    ordinary: { head_branch: "feat/example" },
    sha: { head_sha: "invalid" },
    queued: { status: "queued" },
    waiting: { status: "waiting" },
    pending: { status: "pending" },
    requested: { status: "requested" },
  };
  Object.assign(Current, Changes[CaseName] ?? {});
  return {
    CaseName,
    Current,
    Cancelled: [],
    Calls: [],
    EntryNumbers: [],
    RefNames: [],
  };
}

module.exports = { FixtureData };
