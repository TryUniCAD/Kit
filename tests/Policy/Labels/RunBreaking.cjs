const Assert = require("node:assert/strict");
const { readFileSync: ReadFile } = require("node:fs");
const { resolve: ResolvePath } = require("node:path");
const CaseMode = process.argv[2];
const SourceText = ReadFile(
  ResolvePath(
    __dirname,
    "../../../.github/workflows/PullRequestBreakingChange.yml",
  ),
  "utf8",
);
Assert.match(
  SourceText,
  /group: .*github\.event\.pull_request\.number.*github\.event\.action/,
);
Assert.match(SourceText, /cancel-in-progress: true/);
Assert.doesNotMatch(SourceText, /^    needs:/m);
const ScriptText = SourceText.split("          script: |\n")[1].replace(
  /^ {12}/gm,
  "",
);
const PullState = {
  title:
    CaseMode === "breaking" ? "feat!: change contract" : "fix: keep contract",
  body: "",
  labels: CaseMode === "remove" ? [{ name: "Breaking Change" }] : [],
};
const Writes = [];
const Github = {
  rest: {
    pulls: {
      get: async () => ({ data: structuredClone(PullState) }),
    },
    issues: {
      getLabel: async () => ({}),
      addLabels: async (Request) => {
        Writes.push("add");
        PullState.labels = Request.labels.map((LabelName) => ({
          name: LabelName,
        }));
      },
      removeLabel: async () => {
        Writes.push("remove");
        PullState.labels = [];
      },
    },
  },
};
const Context = {
  repo: { owner: "Example", repo: "Kit" },
  payload: {
    pull_request: { number: 1, title: "feat!: stale payload", labels: [] },
  },
};
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction("github", "context", ScriptText)(Github, Context)
  .then(() => {
    Assert.deepEqual(
      Writes,
      CaseMode === "breaking"
        ? ["add"]
        : CaseMode === "remove"
          ? ["remove"]
          : [],
    );
    process.stdout.write(JSON.stringify({ Writes, PullState }));
  })
  .catch((Failure) => {
    process.stderr.write(Failure.stack);
    process.exitCode = 1;
  });
