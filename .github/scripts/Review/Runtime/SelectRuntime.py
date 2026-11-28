import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from CheckPull import CheckPull
from HasReport import HasReport
from ObjectMap import ObjectMap


# queued automatic requests must reuse published receipts without delaying acknowledgement or rotating stale account credentials
def SelectRuntime() -> None:
    Context = ObjectMap(JsonTools.loads(Path("ReviewInput/Context.json").read_text()))
    Evidence = ObjectMap(Context["evidence"])
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    PullData = CheckPull(RepoName, Evidence)
    EventData = ObjectMap(
        JsonTools.loads(Path(OsTools.environ["GITHUB_EVENT_PATH"]).read_text())
    )
    Inputs = ObjectMap(EventData.get("inputs", {}))
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Settings = ObjectMap(Config["AccountReview"])
    Settings["UserId"] = ObjectMap(cast(list[object], Config["Reviewers"])[0])["UserId"]
    ShouldRun = (
        Context.get("mention_comment") is not None
        or str(Inputs.get("force", "false")).lower() == "true"
        or bool(Inputs.get("id"))
        or not HasReport(RepoName, Evidence, Settings, PullData)
    )
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write(f"run={'true' if ShouldRun else 'false'}\n")


if __name__ == "__main__":
    SelectRuntime()
