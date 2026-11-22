const Assert = require("node:assert/strict");
const { CleanRuns } = require("../../../.github/scripts/Queue/CleanRuns.cjs");
const { FixtureData } = require("./FixtureData.cjs");
const Fixture = FixtureData(process.argv[2]);
const Github = {
  graphql: async (Query, Variables) => {
    if (Query.includes("pullRequest(number:")) {
      Fixture.Calls.push("entry");
      Assert.equal(Variables.number, 42);
      if (Fixture.CaseName === "entry-error")
        throw new Error("Entry unavailable");
      return {
        repository: {
          pullRequest:
            Fixture.CaseName === "entry-missing"
              ? null
              : {
                  mergeQueueEntry:
                    Fixture.CaseName === "entry-active"
                      ? { id: "current" }
                      : null,
                },
        },
      };
    }
    Fixture.Calls.push("queue");
    if (Fixture.CaseName === "queue-error")
      throw new Error("Queue unavailable");
    if (Fixture.CaseName === "queue-null")
      return { repository: { mergeQueue: null } };
    const More = Fixture.CaseName === "queue-page" && !Variables.cursor;
    const Active =
      ["queue-active", "queue-page"].includes(Fixture.CaseName) && !More;
    return {
      repository: {
        mergeQueue: {
          entries: {
            nodes:
              Fixture.CaseName === "queue-missing"
                ? [{ headCommit: null }]
                : Active
                  ? [{ headCommit: { oid: Fixture.Current.head_sha } }]
                  : [],
            pageInfo: { hasNextPage: More, endCursor: More ? "next" : null },
          },
        },
      },
    };
  },
  rest: {
    actions: {
      listWorkflowRuns: "list",
      getWorkflowRun: async (Request) => ({
        data: { ...Fixture.Current, id: Request.run_id },
      }),
      cancelWorkflowRun: async (Request) => {
        Fixture.Calls.push("cancel");
        Assert.ok([42, 43].includes(Request.run_id));
        Fixture.Cancelled.push(Request.run_id);
      },
    },
    git: {
      getRef: async (Request) => {
        Fixture.Calls.push("ref");
        Assert.equal(Request.ref, `heads/${Fixture.Current.head_branch}`);
        if (Fixture.CaseName === "ref-active")
          return { data: { object: { sha: Fixture.Current.head_sha } } };
        throw Object.assign(new Error("Reference lookup"), {
          status: Fixture.CaseName === "ref-error" ? 403 : 404,
        });
      },
    },
  },
  paginate: async (Method, Request) => {
    Assert.equal(Method, "list");
    Assert.equal(Request.workflow_id, "MergeQueue.yml");
    Assert.equal(Request.event, "merge_group");
    return Request.status === "in_progress"
      ? Fixture.CaseName === "multiple"
        ? [{ id: 42 }, { id: 43 }]
        : [{ id: 42 }]
      : [];
  },
};

CleanRuns({
  Github,
  Context: {
    repo: { owner: "Example", repo: "Kit" },
    payload: { repository: { id: 1 } },
  },
  Core: { info: () => {} },
})
  .then(() => process.stdout.write(JSON.stringify(Fixture)))
  .catch((ErrorInfo) => {
    process.stdout.write(JSON.stringify(Fixture));
    process.stderr.write(ErrorInfo.message);
    process.exitCode = 1;
  });
