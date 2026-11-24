const Assert = require("node:assert/strict");
const { CleanRuns } = require("../../../.github/scripts/Queue/CleanRuns.cjs");
const { FixtureData } = require("./FixtureData.cjs");
const Fixture = FixtureData(process.argv[2], process.argv[3]);
const Github = {
  graphql: async (Query, Variables) => {
    if (Query.includes("pullRequest(number:")) {
      Fixture.Calls.push("entry");
      Fixture.EntryNumbers.push(Variables.number);
      Assert.ok([42, 43].includes(Variables.number));
      if (Fixture.CaseName === "entry-error")
        throw new Error("Entry unavailable");
      return {
        repository: {
          pullRequest:
            Fixture.CaseName === "entry-missing"
              ? null
              : {
                  mergeQueueEntry: [
                    "entry-active",
                    "entry-unknown",
                    "replacement",
                  ].includes(Fixture.CaseName)
                    ? {
                        headCommit:
                          Fixture.CaseName === "entry-unknown"
                            ? null
                            : {
                                oid:
                                  Fixture.CaseName === "replacement"
                                    ? "c".repeat(40)
                                    : Fixture.Current.head_sha,
                              },
                      }
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
    const ExtraPage = Fixture.CaseName === "queue-page" && !Variables.cursor;
    const Active =
      ["queue-active", "queue-page"].includes(Fixture.CaseName) && !ExtraPage;
    return {
      repository: {
        mergeQueue: {
          entries: {
            nodes:
              Fixture.CaseName === "queue-missing"
                ? [{ headCommit: null }]
                : Fixture.CaseName === "replacement"
                  ? [{ headCommit: { oid: "c".repeat(40) } }]
                  : Active
                    ? [{ headCommit: { oid: Fixture.Current.head_sha } }]
                    : [],
            pageInfo: {
              hasNextPage: ExtraPage,
              endCursor: ExtraPage ? "next" : null,
            },
          },
        },
      },
    };
  },
  rest: {
    actions: {
      listWorkflowRunsForRepo: "list",
      getWorkflowRun: async (Request) => ({
        data: {
          ...Fixture.Current,
          id: Request.run_id,
          head_branch:
            Fixture.CaseName === "multiple"
              ? Fixture.Current.head_branch.replace(
                  "pr-42-",
                  `pr-${Request.run_id}-`,
                )
              : Fixture.CaseName === "replacement" && Request.run_id === 43
                ? `gh-readonly-queue/main/pr-42-${"d".repeat(40)}`
                : Fixture.Current.head_branch,
          head_sha:
            Fixture.CaseName === "replacement" && Request.run_id === 43
              ? "c".repeat(40)
              : Fixture.Current.head_sha,
        },
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
        Fixture.RefNames.push(Request.ref);
        if (Fixture.CaseName !== "multiple")
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
    Assert.equal(Request.workflow_id, undefined);
    Assert.equal(Request.event, "merge_group");
    return Request.status === "in_progress"
      ? ["multiple", "replacement"].includes(Fixture.CaseName)
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
  Logger: { info: () => {} },
})
  .then(() => process.stdout.write(JSON.stringify(Fixture)))
  .catch((ErrorInfo) => {
    process.stdout.write(JSON.stringify(Fixture));
    process.stderr.write(ErrorInfo.message);
    process.exitCode = 1;
  });
