const { ReadAuditRuns } = require("./ReadAuditRuns.cjs");

async function SelectBudget(Github, Context, Logger) {
  let Enabled = false;
  try {
    const Result = await Github.rest.repos.getContent({
      ...Context.repo,
      path: ".github/CiResources.json",
      ref: Context.payload.merge_group.base_sha,
    });
    const Config = JSON.parse(
      Buffer.from(Result.data.content, "base64").toString("utf8"),
    );
    if (
      Config.Version !== 1 ||
      Config.Linux !== 8 ||
      Config.Windows !== 5 ||
      Config.Macos !== 5 ||
      Config.Control !== 2
    )
      throw new Error("Unsupported shared runner budget");
    Enabled = true;
  } catch (ErrorInfo) {
    if (ErrorInfo.status !== 404) throw ErrorInfo;
  }
  const AuditRuns = Enabled && (await ReadAuditRuns(Github, Context.repo));
  const Count = Enabled && !AuditRuns ? 5 : 4;
  Logger.setOutput(
    "native",
    JSON.stringify(
      Array.from({ length: Count }, (Value, Index) => ({
        group: `shard-${Index + 1}`,
        index: Index,
      })),
    ),
  );
  Logger.setOutput("count", String(Count));
  Logger.setOutput("max-tests", Enabled ? "1000" : "1200");
  Logger.setOutput("runtime-target", Enabled ? "1200" : "0");
  Logger.info(
    `Native shards: ${Count}; shared Linux lanes: 8; trusted budget active: ${Enabled}`,
  );
}

module.exports = { SelectBudget };
