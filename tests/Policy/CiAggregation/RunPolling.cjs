const { Aggregate } = require("../../../.github/scripts/CiReports.cjs");
const { BuildReports } = require("./ReportInputs.cjs");

const CaseName = process.argv[2];
const Inputs = BuildReports(
  "queue-run",
  "pending",
  "Merge queue acceptance",
  4,
);
const QueueRun = Inputs.Runs.find(
  (Run) => Run.conclusion === "pending" && Run.status === "in_progress",
);
if (!QueueRun) throw new Error("Fixture has no pending queue run");

const Start = Date.parse("2026-11-26T12:00:00Z");
let Clock = Start;
const RealTimeout = setTimeout;
Date.now = () => Clock;
global.setTimeout = (Callback, Delay) => {
  process.stdout.write(`sleep ${Math.round(Delay / 1000)} s\n`);
  Clock += Delay;
  return RealTimeout(Callback, 0);
};

const Remaining = { pacing: 600, exhausted: 450 }[CaseName] ?? 1000;
let Gates = 0;
const Github = {
  graphql: async () => ({ repository: { mergeQueue: null } }),
  rest: {
    actions: { listWorkflowRunsForRepo: "listWorkflowRunsForRepo" },
    checks: { listForRef: "listForRef" },
    rateLimit: {
      get: async () => ({
        data: {
          resources: {
            core: {
              limit: 1000,
              remaining: Remaining,
              reset: Math.floor(Start / 1000) + 3600,
            },
          },
        },
      }),
    },
  },
  paginate: async (Method) =>
    Method === "listWorkflowRunsForRepo" ? Inputs.Runs : Inputs.Checks,
  request: async (Route, Request) => {
    if (Route !== "GET /repos/{owner}/{repo}/actions/runs")
      throw new Error(`Unexpected request ${Route}`);
    Gates += 1;
    if (Gates === 1) {
      if (Request.headers["if-none-match"])
        throw new Error("First poll must not be conditional");
      return { data: { workflow_runs: Inputs.Runs }, headers: { etag: "W/1" } };
    }
    if (Gates === 2) {
      if (Request.headers["if-none-match"] !== "W/1")
        throw new Error("Later polls must send the previous ETag");
      throw Object.assign(new Error("Not Modified"), { status: 304 });
    }
    if (Gates === 3 && CaseName === "ratelimit")
      throw Object.assign(new Error("API rate limit exceeded"), {
        status: 403,
        response: {
          headers: {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": String(Math.floor(Clock / 1000) + 600),
          },
        },
      });
    if (Gates === 3 && CaseName === "secondary")
      throw Object.assign(
        new Error("You have exceeded a secondary rate limit"),
        {
          status: 429,
          response: { headers: { "retry-after": "60" } },
        },
      );
    if (Gates === 3 && CaseName === "forbidden")
      throw Object.assign(new Error("Resource not accessible by integration"), {
        status: 403,
        response: { headers: {} },
      });
    QueueRun.status = "completed";
    QueueRun.conclusion = CaseName === "failure" ? "failure" : "success";
    return { data: { workflow_runs: Inputs.Runs }, headers: { etag: "W/2" } };
  },
};

const Summary = {
  addHeading(Value) {
    process.stdout.write(`${Value}\n`);
    return this;
  },
  addTable() {
    return this;
  },
  async write() {},
};
Aggregate({
  github: Github,
  context: {
    eventName: "merge_group",
    sha: "a".repeat(40),
    runId: 500,
    repo: { owner: "TryUniCAD", repo: "Kit" },
    payload: {
      repository: { id: 1 },
      merge_group: {
        base_ref: "refs/heads/main",
        head_sha: "a".repeat(40),
        head_commit: { timestamp: new Date(Start).toISOString() },
      },
    },
  },
  core: {
    summary: Summary,
    info: (Value) => process.stdout.write(`${Value}\n`),
  },
})
  .then(() => process.stdout.write(`gates ${Gates}\n`))
  .catch((Failure) => {
    process.stderr.write(`${Failure.message}\n`);
    process.exitCode = 1;
  });
