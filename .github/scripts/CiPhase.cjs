async function SetPhase({ github: Github, context: Context, core: Core }) {
  const BaseSha =
    Context.payload.pull_request?.base.sha ??
    Context.payload.merge_group?.base_sha;
  if (!BaseSha) throw new Error("Validation phase requires an event base SHA");
  let Phase = "legacy";
  try {
    const Response = await Github.rest.repos.getContent({
      ...Context.repo,
      path: ".github/CiPhases.json",
      ref: BaseSha,
    });
    const Config = JSON.parse(
      Buffer.from(Response.data.content, "base64").toString("utf8"),
    );
    if (Config.Version !== 1)
      throw new Error("Unsupported CI phase configuration");
    Phase = Context.eventName;
  } catch (ErrorInfo) {
    if (ErrorInfo.status !== 404) throw ErrorInfo;
  }
  Core.setOutput("phase", Phase);
  Core.info(`Validation phase: ${Phase}`);
}

module.exports = { SetPhase };
