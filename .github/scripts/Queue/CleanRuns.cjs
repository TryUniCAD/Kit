const { CancelStale } = require("./CancelStale.cjs");
const { QueueHeads } = require("./QueueHeads.cjs");

async function CleanRuns({ Github, Context, Core }) {
  const Heads = await QueueHeads(Github, Context.repo);
  for (const Status of [
    "queued",
    "in_progress",
    "waiting",
    "pending",
    "requested",
  ]) {
    const Runs = await Github.paginate(Github.rest.actions.listWorkflowRuns, {
      ...Context.repo,
      workflow_id: "MergeQueue.yml",
      event: "merge_group",
      status: Status,
      per_page: 100,
    });
    for (const Listed of Runs) {
      const { data: Current } = await Github.rest.actions.getWorkflowRun({
        ...Context.repo,
        run_id: Listed.id,
      });
      if (await CancelStale(Github, Context, Current, Heads))
        Core.info(
          `Cancelled abandoned queue run ${Current.id} at ${Current.head_sha}`,
        );
      else Core.info(`Preserved queue run ${Current.id}`);
    }
  }
}

module.exports = { CleanRuns };
