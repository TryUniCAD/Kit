const { ReadExpansion } = require("./ReadExpansion.cjs");
const { ReadAuditRuns } = require("./ReadAuditRuns.cjs");

async function SelectBudget(Github, Context, Logger) {
  let Enabled = false;
  let LaneSets = 1;
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
      !(
        (Config.Version === 1 &&
          Config.Linux === 8 &&
          Config.Windows === 5 &&
          Config.Macos === 5) ||
        (Config.Version === 2 &&
          Config.Linux === 16 &&
          Config.Windows === 5 &&
          Config.Macos === 5) ||
        (Config.Version === 3 &&
          Config.LaneSets === 2 &&
          Config.Linux === 32 &&
          Config.Windows === 9 &&
          Config.Macos === 5) ||
        (Config.Version === 4 &&
          Config.Plan === "Enterprise" &&
          Config.LaneSets === 4 &&
          Config.Linux === 64 &&
          Config.Windows === 20 &&
          Config.WindowsCompatibility === 16 &&
          Config.Macos === 20)
      ) ||
      Config.Control !== 2
    )
      throw new Error("Unsupported shared runner budget");
    Enabled = true;
    LaneSets = Config.LaneSets ?? 1;
  } catch (ErrorInfo) {
    if (ErrorInfo.status !== 404) throw ErrorInfo;
  }
  const Expanded =
    Enabled && (await ReadExpansion(Github, Context.repo, Logger));
  const AuditRuns = Expanded && (await ReadAuditRuns(Github, Context.repo));
  const Count = Expanded && !AuditRuns ? 5 : 4;
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
  Logger.setOutput("max-tests", Expanded ? "1000" : "1200");
  Logger.setOutput("runtime-target", Expanded ? "1200" : "0");
  Logger.info(
    `Native shards: ${Count}; candidate lane sets: ${LaneSets}; trusted budget active: ${Enabled}`,
  );
}

module.exports = { SelectBudget };
