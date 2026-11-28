import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path

from ObjectMap import ObjectMap


# account credentials belong only to the isolated model container and must never become review artifacts
def RunModel() -> None:
    ContextText = Path("ReviewInput/Context.json").read_text()
    Runtime = ObjectMap(ObjectMap(JsonTools.loads(ContextText))["review_runtime"])
    AuthPath = Path(OsTools.environ["RUNNER_TEMP"]) / "ReviewAuth"
    AuthPath.mkdir(mode=0o700)
    AuthFile = AuthPath / "auth.json"
    AuthFile.write_text(OsTools.environ["CODEX_AUTH_JSON"])
    AuthFile.chmod(0o600)
    AuthData = ObjectMap(JsonTools.loads(AuthFile.read_text()))
    if AuthData.get("auth_mode") != "chatgpt" or not ObjectMap(AuthData["tokens"]).get(
        "refresh_token"
    ):
        raise ValueError("CI needs a dedicated managed ChatGPT login")
    OutputPath = Path("ReviewOutput").resolve()
    OutputPath.mkdir()
    Prompt = Path(".github/scripts/Review/ReviewPrompt.md").read_text()
    Prompt += "\n\nUntrusted review input follows:\n" + ContextText
    Arguments = [
        "docker",
        "run",
        "--rm",
        "--read-only",
        "--user",
        f"{OsTools.getuid()}:{OsTools.getgid()}",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=128",
        "--memory=4g",
        "--cpus=2",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=256m",
        "--interactive",
        "--mount",
        f"type=bind,src={AuthPath},dst=/auth",
        "--mount",
        f"type=bind,src={OutputPath},dst=/output",
        "--mount",
        f"type=bind,src={Path('.github/scripts/Review/ReviewSchema.json').resolve()},dst=/schema/ReviewSchema.json,readonly",
        "--env",
        "CODEX_HOME=/auth",
        "--env",
        "HOME=/tmp",
        "--workdir",
        "/tmp",
        "kit-review-runtime",
        "codex",
        "exec",
        "--model",
        str(Runtime["model"]),
        "-c",
        f'model_reasoning_effort="{Runtime["reasoning_effort"]}"',
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "apps",
        "--disable",
        "plugins",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "code_mode_host",
        "--disable",
        "multi_agent",
        "--disable",
        "view_image",
        "--disable",
        "hooks",
        "-c",
        'web_search="disabled"',
        "-c",
        'cli_auth_credentials_store="file"',
        "--output-schema",
        "/schema/ReviewSchema.json",
        "--output-last-message",
        "/output/Report.json",
        "-",
    ]
    ProcessTools.run(
        Arguments,
        input=Prompt,
        text=True,
        check=True,
        timeout=1800,
        stdout=ProcessTools.DEVNULL,
        stderr=ProcessTools.DEVNULL,
    )


if __name__ == "__main__":
    RunModel()
