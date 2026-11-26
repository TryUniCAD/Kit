const KWorkflowPaths = Object.freeze([
  ".github/workflows/MergeQueue.yml",
  // CI Agg serializes queue runs on one concurrency group, so an abandoned run blocks every later candidate.
  ".github/workflows/PullRequest.yml",
  ".github/workflows/WorkflowQuality.yml",
]);

module.exports = { KWorkflowPaths };
