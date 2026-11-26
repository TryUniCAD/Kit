async function SelectLaneSet(Github, Context, Logger) {
  const HeadSha = Context.payload.merge_group?.head_sha;
  if (Context.eventName !== "merge_group") {
    Logger.setOutput("prefix", "");
    return;
  }
  if (!/^[0-9a-f]{40}$/.test(HeadSha ?? ""))
    throw new Error("Lane selection requires the merge-group head SHA");
  const Result = await Github.graphql(
    `query ($Owner: String!, $Name: String!, $Sha: GitObjectID!) {
      repository(owner: $Owner, name: $Name) {
        object(oid: $Sha) { ... on Commit { history(first: 1) { totalCount } } }
      }
    }`,
    { Owner: Context.repo.owner, Name: Context.repo.repo, Sha: HeadSha },
  );
  const Count = Result.repository?.object?.history?.totalCount;
  if (!Number.isInteger(Count) || Count < 1)
    throw new Error("Lane selection could not count candidate ancestors");
  const Prefix = Count % 2 === 0 ? "" : "B-";
  Logger.setOutput("prefix", Prefix);
  Logger.info(
    `Candidate ${HeadSha} has ${Count} ancestors; lane set ${Prefix ? "B" : "A"}`,
  );
}

module.exports = { SelectLaneSet };
