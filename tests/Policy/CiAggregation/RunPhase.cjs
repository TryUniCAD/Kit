const { SetPhase } = require("../../../.github/scripts/CiPhase.cjs");

const CaseMode = process.argv[2];
const EventName = CaseMode === "queue" ? "merge_group" : "pull_request";
const BaseSha = "b".repeat(40);
const Context = {
  eventName: EventName,
  repo: { owner: "TryUniCAD", repo: "Kit" },
  payload: {
    pull_request:
      EventName === "pull_request" ? { base: { sha: BaseSha } } : null,
    merge_group: EventName === "merge_group" ? { base_sha: BaseSha } : null,
  },
};
const Github = {
  rest: {
    repos: {
      async getContent(Request) {
        if (Request.ref !== BaseSha || Request.path !== ".github/CiPhases.json")
          throw new Error("Phase selection used different inputs");
        if (CaseMode === "legacy" || CaseMode === "denied")
          throw Object.assign(new Error("Unavailable phase marker"), {
            status: CaseMode === "legacy" ? 404 : 403,
          });
        const Version = CaseMode === "invalid" ? 2 : 1;
        return {
          data: {
            content: Buffer.from(JSON.stringify({ Version })).toString(
              "base64",
            ),
          },
        };
      },
    },
  },
};
SetPhase({
  github: Github,
  context: Context,
  core: {
    setOutput(Name, Value) {
      process.stdout.write(`${Name}=${Value}\n`);
    },
    info(Value) {
      process.stdout.write(`${Value}\n`);
    },
  },
}).catch((Failure) => {
  process.stderr.write(`${Failure.message}\n`);
  process.exitCode = 1;
});
