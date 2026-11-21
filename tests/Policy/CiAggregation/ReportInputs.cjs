const { BuildExpected } = require("./ExpectedChecks.cjs");
const { BuildReviews } = require("./ReviewReports.cjs");

function BuildReports(CaseMode, Verdict, CheckName) {
  const IsQueue = CaseMode.startsWith("queue");
  const HeadSha = "a".repeat(40);
  const Built = BuildExpected(IsQueue, HeadSha);
  const Runs = Built.Runs;
  const Checks = Built.Checks;
  const Expected = Checks.map(({ name, html_url }) => ({ name, html_url }));
  const Files =
    CaseMode === "quality-docs"
      ? [{ filename: "Documentation/Index.md", status: "modified" }]
      : [{ filename: "src/Example.py", status: "modified" }];
  const Reviews = BuildReviews(Verdict);
  const Statuses = Reviews.Statuses;

  if (CaseMode === "check")
    Checks.find((Check) => Check.name === CheckName).conclusion = Verdict;
  if (CaseMode === "status")
    Statuses.push({
      id: 900,
      context: "Ruff",
      creator: { id: 900, login: "build-service" },
      state: "failure",
    });

  const Ruff = Checks.find((Check) => Check.name === "Ruff");
  if (CaseMode === "external")
    Checks.push({
      ...Ruff,
      id: 901,
      app: { id: 901, slug: "external-ci" },
      conclusion: "failure",
    });
  if (CaseMode === "unlisted-job")
    Checks.push({
      ...Ruff,
      id: 902,
      name: "Unlisted job",
      conclusion: "failure",
    });
  if (CaseMode === "unlisted-run" || CaseMode === "spoof") {
    Runs.push({
      id: 903,
      check_suite_id: 903,
      head_sha: HeadSha,
      event: "pull_request",
      path: ".github/workflows/Unlisted.yml",
      name: "Unlisted workflow",
      status: "completed",
      conclusion: "failure",
    });
    Checks.push({
      ...Ruff,
      id: 903,
      check_suite: { id: 903 },
      conclusion: CaseMode === "spoof" ? "success" : "failure",
    });
  }

  if (CaseMode === "queue" || CaseMode === "queue-run") {
    const Check = Checks.find((Item) => Item.name === CheckName);
    const Run = Runs.find(
      (Item) => Item.check_suite_id === Check.check_suite.id,
    );
    const Target = CaseMode === "queue-run" ? Run : Check;
    Target.status = Verdict === "pending" ? "in_progress" : "completed";
    Target.conclusion = Verdict;
  }

  return {
    Checks: [
      ...Checks.filter(
        (Check) =>
          !(
            CaseMode === "queue-missing" &&
            Check.name === "Merge queue acceptance"
          ) && !(CaseMode === "spoof" && Check === Ruff),
      ),
      ...Reviews.Checks,
    ],
    Statuses,
    Runs,
    Expected,
    Files,
    Forked: CaseMode === "quality-fork",
  };
}

module.exports = { BuildReports };
