const { CancelStale } = require("./CancelStale.cjs");
const { QueueHeads } = require("./QueueHeads.cjs");

async function CleanRuns({ Github, Context, Logger }) {
  const Heads = await QueueHeads(Github, Context.repo);
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
        ...Context.repo,
        workflow_id: "MergeQueue.yml",
        event: "merge_group",
        status: Status,
        per_page: 100,
      },
    );
    for (const Listed of RunList) {
      const { data: Current } = await Github.rest.actions.getWorkflowRun({
        ...Context.repo,
        run_id: Listed.id,
      });
      if (await CancelStale(Github, Context, Current, Heads))
        Logger.info(
          `Cancelled abandoned queue run ${Current.id} at ${Current.head_sha}`,
        );
      else Logger.info(`Preserved queue run ${Current.id}`);
    }
  }
}

module.exports = { CleanRuns };
