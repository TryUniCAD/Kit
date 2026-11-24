const { readFileSync: ReadFile } = require("node:fs");
const { resolve: ResolvePath } = require("node:path");
const Assert = require("node:assert/strict");
const {
  SelectBudget,
} = require("../../../.github/scripts/Scheduling/SelectBudget.cjs");
const {
  WaitForQueue,
} = require("../../../.github/scripts/Scheduling/WaitForQueue.cjs");
const CaseName = process.argv[2];
const Outputs = {};
let Ticks = 0;
let Pauses = 0;
let Requests = 0;
const Github = {
  graphql: async () => {
    Requests += 1;
    if (CaseName === "admit-error")
      throw new Error("Admission API unavailable");
    return {
      repository: {
        mergeQueue: {
          entries: {
            totalCount:
              ["admit-busy", "admit-timeout"].includes(CaseName) && !Pauses
                ? 1
                : 0,
          },
        },
      },
    };
  },
  rest: {
    repos: {
      getContent: async (Request) => {
        Assert.equal(Request.ref, "trusted-base");
        if (CaseName === "budget-legacy")
          throw Object.assign(new Error("Missing marker"), { status: 404 });
        if (CaseName === "budget-error")
          throw Object.assign(new Error("Budget API unavailable"), {
            status: 403,
          });
        return {
          data: {
            content: Buffer.from(
              JSON.stringify({
                ...JSON.parse(
                  ReadFile(
                    ResolvePath(__dirname, "../../../.github/CiResources.json"),
                    "utf8",
                  ),
                ),
                ...(CaseName === "budget-audit"
                  ? { Version: 1, Linux: 8 }
                  : {}),
                ...(CaseName === "budget-invalid" ? { Version: 3 } : {}),
              }),
            ).toString("base64"),
          },
        };
      },
    },
    actions: { listWorkflowRuns: "runs" },
  },
  paginate: async (Method, Request) => {
    Requests += 1;
    if (Method === "GET /repos/{owner}/{repo}/rules/branches/{branch}") {
      Assert.equal(Request.branch, "main");
      if (CaseName === "budget-rules-error")
        throw new Error("Rules unavailable");
      return [
        {
          type: "merge_queue",
          parameters: {
            max_entries_to_build:
              CaseName === "budget-uncontrolled"
                ? 25
                : CaseName === "budget-audit"
                  ? 1
                  : 2,
            min_entries_to_merge: CaseName === "budget-minimum" ? 2 : 1,
            min_entries_to_merge_wait_minutes:
              CaseName === "budget-wait" ? 10 : 0,
          },
        },
      ];
    }
    Assert.equal(Method, "runs");
    Assert.equal(Request.workflow_id, "MergeQueue.yml");
    if (CaseName === "budget-audit" && Request.status === "in_progress")
      return [{ event: "workflow_dispatch" }];
    if (
      CaseName === "admit-stale" &&
      Request.status === "in_progress" &&
      !Pauses
    )
      return [{ event: "merge_group" }];
    return [];
  },
};
const Context = {
  repo: { owner: "Example", repo: "Kit" },
  payload: { merge_group: { base_sha: "trusted-base" } },
};
const Logger = {
  info: () => {},
  warning: () => {},
  setOutput: (OutputName, Value) => {
    Outputs[OutputName] = Value;
  },
};
const Operation = CaseName.startsWith("budget-")
  ? SelectBudget(Github, Context, Logger)
  : WaitForQueue(
      Github,
      Context,
      Logger,
      async (Delay) => {
        Assert.ok(Delay > 0 && Delay <= 30000);
        Pauses += 1;
        Ticks += CaseName === "admit-timeout" ? 3600000 : Delay;
      },
      () => Ticks,
    );
Operation.then(() =>
  process.stdout.write(JSON.stringify({ Outputs, Pauses, Requests })),
).catch((ErrorInfo) => {
  process.stderr.write(ErrorInfo.message);
  process.exitCode = 1;
});
