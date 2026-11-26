const Fs = require("node:fs");
const { CiWorkflows } = require("./CiAllowlist.cjs");

async function ReadReports(Github, Context, Refs, Workflows) {
  const Repository = Context.repo;
  const LatestRuns = new Map();
  const Checks = [];
  const ReportRefs = new Set(Refs);
  for (const Ref of ReportRefs) {
    const Runs = await Github.paginate(
      Github.rest.actions.listWorkflowRunsForRepo,
      {
        ...Repository,
        head_sha: Ref,
        per_page: 100,
      },
    );
    for (const Run of Runs) {
      const Workflow = Run.path?.split("@")[0];
      const Spec = Workflows.get(Workflow);
      if (
        !Spec ||
        Run.id === Context.runId ||
        Run.head_sha !== Ref ||
        Spec.event !== Run.event
      )
        continue;
      const Key = `${Workflow}:${Ref}`;
      if (!LatestRuns.has(Key) || LatestRuns.get(Key).id < Run.id)
        LatestRuns.set(Key, { ...Run, workflow: Workflow });
    }
    Checks.push(
      ...(await Github.paginate(Github.rest.checks.listForRef, {
        ...Repository,
        ref: Ref,
        filter: "latest",
        per_page: 100,
      })),
    );
  }

  const RunsBySuite = new Map(
    [...LatestRuns.values()].map((Run) => [Run.check_suite_id, Run]),
  );
  const Rows = [];
  const Seen = new Set();
  for (const Check of Checks) {
    if (
      Seen.has(Check.id) ||
      Check.app?.id !== 15368 ||
      !ReportRefs.has(Check.head_sha)
    )
      continue;
    const Run = RunsBySuite.get(Check.check_suite?.id);
    if (!Run) continue;
    const Spec = Workflows.get(Run.workflow);
    const Required = Spec.required.includes(Check.name);
    const Preflight = Spec.preflight && Check.name === Spec.preflight;
    const Matched = Spec.matching?.some((Pattern) => Pattern.test(Check.name));
    if (
      !Required &&
      !Preflight &&
      !Matched &&
      !Spec.optional?.includes(Check.name)
    )
      continue;
    Seen.add(Check.id);
    const AllowedSkip = Spec.skip?.includes(Check.name);
    Rows.push({
      name: Check.name,
      workflow: Run.workflow,
      state:
        Check.status !== "completed"
          ? "pending"
          : Check.conclusion === "success" ||
              (Check.conclusion === "skipped" && AllowedSkip)
            ? "pass"
            : "fail",
      conclusion: Check.conclusion,
      url: Check.html_url || Check.details_url || "",
    });
  }
  for (const Run of LatestRuns.values()) {
    if (Run.status !== "completed" || Run.conclusion !== "success")
      Rows.push({
        name: Run.name,
        state: Run.status !== "completed" ? "pending" : "fail",
        conclusion: Run.conclusion,
        url: Run.html_url,
      });
  }
  for (const [Workflow, Spec] of Workflows) {
    const Expected = Spec.preflight
      ? [...Spec.required, Spec.preflight]
      : Spec.required;
    for (const Name of Expected) {
      if (!Rows.some((Row) => Row.name === Name && Row.workflow === Workflow))
        Rows.push({
          name: Name,
          state: "pending",
          conclusion: "missing",
          url: "",
        });
    }
    if (!Spec.expected) continue;
    const HasRun = [...LatestRuns.values()].some(
      (Run) => Run.workflow === Workflow,
    );
    const HasJob = Rows.some((Row) => Row.workflow === Workflow);
    if (!HasRun || !HasJob)
      Rows.push({
        name: HasRun ? `${Spec.expected} analysis` : Spec.expected,
        state: "pending",
        conclusion: "missing",
        url: "",
      });
  }
  return Rows;
}

async function PullMergeRef(Github, Context) {
  const Pull = Context.payload.pull_request;
  const Candidates = [
    Context.eventName === "pull_request" ? Context.sha : null,
    Pull.merge_commit_sha,
  ];
  const Current = (
    await Github.rest.pulls.get({ ...Context.repo, pull_number: Pull.number })
  ).data;
  if (Current.head.sha === Pull.head.sha && Current.base.sha === Pull.base.sha)
    Candidates.push(Current.merge_commit_sha);
  for (const Sha of new Set(Candidates)) {
    if (typeof Sha !== "string" || !/^[0-9a-f]{40}$/.test(Sha)) continue;
    let Commit;
    try {
      Commit = (
        await Github.rest.git.getCommit({ ...Context.repo, commit_sha: Sha })
      ).data;
    } catch (ErrorInfo) {
      if (ErrorInfo.status === 404) continue;
      throw ErrorInfo;
    }
    if (
      Commit.parents.some((Parent) => Parent.sha === Pull.head.sha) &&
      Commit.parents.some((Parent) => Parent.sha === Pull.base.sha)
    )
      return Sha;
  }
  return null;
}

function PollDelay(IsPull, Context) {
  if (IsPull) return 30000;
  const Created = Date.parse(
    Context.payload.merge_group?.head_commit?.timestamp ?? "",
  );
  const Idle = Number.isNaN(Created) ? 0 : Created + 10 * 60000 - Date.now();
  return Math.max(120000, Idle);
}

async function Aggregate({ github: Github, context: Context, core: Core }) {
  const IsPull = ["pull_request", "pull_request_target"].includes(
    Context.eventName,
  );
  const ReportMerge = IsPull ? await PullMergeRef(Github, Context) : null;
  const Refs = IsPull
    ? [
        Context.payload.pull_request.head.sha,
        ...(ReportMerge ? [ReportMerge] : []),
      ]
    : [Context.sha];
  const Workflows = CiWorkflows(
    IsPull,
    false,
    Context.payload.action === "opened",
  );
  const Deadline = Date.now() + 80 * 60000;
  let Rows;
  for (;;) {
    if (IsPull) {
      const Current = (
        await Github.rest.pulls.get({
          ...Context.repo,
          pull_number: Context.payload.pull_request.number,
        })
      ).data;
      if (
        Current.state !== "open" ||
        Current.head.sha !== Context.payload.pull_request.head.sha
      )
        throw new Error("The PR head changed during CI aggregation");
    }
    Rows = await ReadReports(Github, Context, Refs, Workflows);
    const Failed = Rows.filter((Row) => Row.state === "fail");
    if (Failed.length) {
      await Core.summary
        .addHeading("CI failed")
        .addTable([
          ["Check", "Conclusion", "Report"],
          ...Failed.map((Row) => [
            Row.name,
            Row.conclusion || "unknown",
            Row.url,
          ]),
        ])
        .write();
      throw new Error(`CI failed: ${Failed.map((Row) => Row.name).join(", ")}`);
    }
    const Pending = Rows.filter((Row) => Row.state === "pending");
    if (!Pending.length) break;
    if (Date.now() >= Deadline)
      throw new Error(
        `CI aggregation timed out waiting for: ${Pending.map((Row) => Row.name).join(", ")}`,
      );
    Core.info(`Waiting for ${Pending.map((Row) => Row.name).join(", ")}`);
    await new Promise((Resolve) =>
      setTimeout(Resolve, PollDelay(IsPull, Context)),
    );
  }
  await Core.summary
    .addHeading("CI passed")
    .addTable([
      ["Check", "Conclusion", "Report"],
      ...Rows.map((Row) => [Row.name, Row.conclusion || "unknown", Row.url]),
    ])
    .write();
  if (IsPull) {
    const Pull = Context.payload.pull_request;
    const Head = (
      await Github.rest.git.getCommit({
        ...Context.repo,
        commit_sha: Pull.head.sha,
      })
    ).data;
    const Comparison = await Github.rest.repos.compareCommits({
      ...Context.repo,
      base: Pull.base.sha,
      head: Pull.head.sha,
    });
    const Directory = "PrCiEvidence";
    Fs.mkdirSync(Directory, { recursive: true });
    Fs.writeFileSync(
      "PrCiEvidence/Evidence.json",
      JSON.stringify(
        {
          format: "pr-head-tree-v1",
          workflow_event: Context.eventName,
          repository_id: Context.payload.repository.id,
          head_repository_id: Pull.head.repo.id,
          pull_number: Pull.number,
          head_sha: Pull.head.sha,
          base_sha: Pull.base.sha,
          head_tree_sha: Head.tree.sha,
          base_is_ancestor: ["ahead", "identical"].includes(
            Comparison.data.status,
          ),
          report_merge_sha: ReportMerge,
          run_id: Context.runId,
          run_attempt: Number(process.env.GITHUB_RUN_ATTEMPT),
        },
        null,
        2,
      ),
    );
  }
}

module.exports = { Aggregate };
