const Fs = require("node:fs");
const Path = require("node:path");
const { ExpandGroups } = require("./ExpandGroups.cjs");

const WorkflowDir = Path.resolve(__dirname, "../../../.github/workflows");

function ReadWorkflows(IsQueue, NativeCount) {
  const Workflows = [];
  for (const File of Fs.readdirSync(WorkflowDir).sort()) {
    if (!/\.ya?ml$/.test(File) || File === "PullRequest.yml") continue;
    const Source = Fs.readFileSync(Path.join(WorkflowDir, File), "utf8");
    const [Header, Jobs] = Source.split(/^jobs:\s*$/m);
    const Triggers = Header.match(/^on:\n([\s\S]*?)(?=^\S)/m)?.[1] ?? "";
    const Phase = IsQueue
      ? /^  (merge_group):/m
      : /^  (pull_request|pull_request_target):/m;
    const Event = Triggers.match(Phase)?.[1];
    if (!Event) continue;
    const Blocks = Jobs?.split(/^  [\w-]+:[ \t]*$/m).slice(1) ?? [];
    if (!Blocks.length) throw new Error(`No jobs found in ${File}`);
    const Deferred = new Set();
    const Names = Blocks.flatMap((Block) => {
      const Name = Block.match(/^    name: (.+)$/m)?.[1];
      if (!Name) throw new Error(`Unnamed CI job in ${File}`);
      const Matrix = "Analyze ${{ matrix.language }}";
      const ShardMatrix = "Test suite / Shard (${{ matrix.shard }})";
      const GroupMatrix = "${{ matrix.group }}";
      const WrongPhase = IsQueue ? "pull_request" : "merge_group";
      if (Block.includes(`outputs.phase == '${WrongPhase}'`))
        Deferred.add(Name);
      if (Name.includes(GroupMatrix)) {
        if ((!IsQueue && File === "MergeQueue.yml") || Deferred.has(Name))
          return [Name];
        return ExpandGroups(Block, NativeCount).map((Group) =>
          Name.replace(GroupMatrix, Group),
        );
      }
      if (IsQueue && Name === ShardMatrix)
        return [1, 2, 3].map((Index) => `Test suite / Shard (${Index})`);
      if (!IsQueue || Name !== Matrix) return [Name];
      return [...Block.matchAll(/^\s+- language: ([\w-]+)$/gm)].map(
        ([, Language]) => `Analyze ${Language}`,
      );
    });
    Workflows.push({
      path: `.github/workflows/${File}`,
      event: Event,
      name: Header.match(/^name: (.+)$/m)?.[1] ?? File,
      jobs: Names,
      deferred: Deferred,
    });
  }
  return Workflows;
}

function BuildExpected(IsQueue, HeadSha, NativeCount = 4) {
  const Runs = [];
  const Checks = [];
  for (const Workflow of ReadWorkflows(IsQueue, NativeCount)) {
    const Suite = Runs.length + 10;
    Runs.push({
      id: Suite,
      check_suite_id: Suite,
      head_sha: HeadSha,
      event: Workflow.event,
      path: Workflow.path,
      name: Workflow.name,
      status: "completed",
      conclusion: "success",
    });
    for (const Name of Workflow.jobs) {
      const Skipped =
        Workflow.deferred.has(Name) ||
        (!IsQueue &&
          Workflow.name === "Merge queue" &&
          Name !== "Merge queue acceptance");
      Checks.push({
        id: Checks.length + 1,
        name: Name,
        head_sha: HeadSha,
        app: { id: 15368, slug: "github-actions" },
        check_suite: { id: Suite },
        status: "completed",
        conclusion: Skipped ? "skipped" : "success",
        html_url: `https://github.example/jobs/${Checks.length + 1}`,
      });
    }
  }
  return { Runs, Checks };
}

module.exports = { BuildExpected };
