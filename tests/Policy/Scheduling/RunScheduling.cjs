const { readFileSync: ReadFile } = require("node:fs");
const { resolve: ResolvePath } = require("node:path");
const Assert = require("node:assert/strict");
const {
  SelectBudget,
} = require("../../../.github/scripts/Scheduling/SelectBudget.cjs");
const {
  WaitForQueue,
} = require("../../../.github/scripts/Scheduling/WaitForQueue.cjs");
const {
  SelectLaneSet,
} = require("../../../.github/scripts/Scheduling/SelectLaneSet.cjs");
const CaseName = process.argv[2];
const Outputs = {};
let Ticks = 0;
let Pauses = 0;
let Requests = 0;
const Github = {
  graphql: async (Query, Variables) => {
    Requests += 1;
    if (CaseName === "admit-error")
      throw new Error("Admission API unavailable");
    if (CaseName.startsWith("lanes-")) {
      Assert.equal(Variables.Sha, "c".repeat(40));
      if (CaseName === "lanes-error") throw new Error("Lane API unavailable");
      return {
        repository: {
          object:
            CaseName === "lanes-missing"
              ? null
              : {
                  history: {
                    totalCount:
                      1000 +
                      Math.max(
                        0,
                        ["lanes-a", "lanes-b", "lanes-c", "lanes-d"].indexOf(
                          CaseName,
                        ),
                      ),
                  },
                },
        },
      };
    }
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
                  ? { Version: 1, Linux: 8, Windows: 5, Macos: 5 }
                  : {}),
                ...(["budget-previous", "budget-previous-minimum"].includes(
                  CaseName,
                )
                  ? { Version: 2, Linux: 16, Windows: 5, Macos: 5 }
                  : {}),
                ...(CaseName === "budget-team"
                  ? {
                      Version: 3,
                      Plan: undefined,
                      LaneSets: 2,
                      Linux: 32,
                      Windows: 9,
                      WindowsCompatibility: 4,
                      Macos: 5,
                    }
                  : {}),
                ...(CaseName === "budget-invalid" ? { Version: 6 } : {}),
                ...(CaseName === "budget-team-macos" ? { Macos: 5 } : {}),
                ...(CaseName === "budget-single" ? { Total: 501 } : {}),
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
              CaseName === "budget-live"
                ? 25
                : CaseName === "budget-uncontrolled"
                  ? 101
                  : CaseName === "budget-five"
                    ? 5
                    : CaseName === "budget-audit"
                      ? 1
                      : CaseName === "budget-team"
                        ? 2
                        : 100,
            min_entries_to_merge: [
              "budget-minimum",
              "budget-live",
              "budget-previous-minimum",
            ].includes(CaseName)
              ? 2
              : 1,
            min_entries_to_merge_wait_minutes: [
              "budget-wait",
              "budget-live",
            ].includes(CaseName)
              ? 10
              : 0,
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
  eventName: CaseName === "lanes-pull" ? "pull_request" : "merge_group",
  repo: { owner: "Example", repo: "Kit" },
  payload: {
    merge_group:
      CaseName === "lanes-pull"
        ? null
        : { base_sha: "trusted-base", head_sha: "c".repeat(40) },
  },
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
  : CaseName.startsWith("lanes-")
    ? SelectLaneSet(Github, Context, Logger)
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
