async function QueueHeads(Github, RepoInfo) {
  const Heads = new Set();
  let Cursor = null;
  do {
    const Result = await Github.graphql(
      `query($owner:String!, $repo:String!, $cursor:String) {
        repository(owner:$owner, name:$repo) {
          mergeQueue(branch:"main") {
            entries(first:100, after:$cursor) {
              nodes { headCommit { oid } }
              pageInfo { hasNextPage endCursor }
            }
          }
        }
      }`,
      { ...RepoInfo, cursor: Cursor },
    );
    const Entries = Result.repository?.mergeQueue?.entries;
    if (!Entries || Entries.nodes.some((Entry) => !Entry?.headCommit?.oid))
      throw new Error("Queue head evidence unavailable; preserve all runs");
    for (const Entry of Entries.nodes) Heads.add(Entry.headCommit.oid);
    Cursor = Entries.pageInfo.hasNextPage ? Entries.pageInfo.endCursor : null;
    if (Entries.pageInfo.hasNextPage && !Cursor)
      throw new Error("Queue pagination evidence unavailable");
  } while (Cursor);
  return Heads;
}

module.exports = { QueueHeads };
