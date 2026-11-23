async function ReadExpansion(Github, RepoInfo, Logger) {
  try {
    const Rules = await Github.paginate(
      "GET /repos/{owner}/{repo}/rules/branches/{branch}",
      { ...RepoInfo, branch: "main", per_page: 100 },
    );
    const Queues = Rules.filter((Rule) => Rule.type === "merge_queue");
    return (
      Queues.length === 1 &&
      Queues[0].parameters.max_entries_to_build === 1 &&
      Queues[0].parameters.min_entries_to_merge === 1 &&
      Queues[0].parameters.min_entries_to_merge_wait_minutes === 0
    );
  } catch (ErrorInfo) {
    Logger.warning(
      `Live queue rules unavailable; shard expansion disabled: ${ErrorInfo.message}`,
    );
    return false;
  }
}

module.exports = { ReadExpansion };
