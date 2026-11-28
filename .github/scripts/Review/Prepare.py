import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path
from typing import cast

from ObjectMap import ObjectMap
from CheckPull import CheckPull
from SelectEvidence import SelectEvidence
from WaitForCi import WaitForCi
from IsContextReady import IsContextReady


# untrusted workflow inputs must be checked before any account credential is restored
def PrepareRun() -> None:
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    RequestPath = Path("ReviewRequest/Event.json")
    EventData = ObjectMap(
        JsonTools.loads(
            (
                RequestPath
                if RequestPath.exists()
                else Path(OsTools.environ["GITHUB_EVENT_PATH"])
            ).read_text()
        )
    )
    RequestId = (
        int(str(ObjectMap(EventData["comment"])["id"]))
        if "comment" in EventData
        else None
    )
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Settings = ObjectMap(Config["AccountReview"])
    Reviewer = ObjectMap(cast(list[object], Config["Reviewers"])[0])
    Settings = {**Settings, "UserId": Reviewer["UserId"]}
    Evidence = SelectEvidence(RepoName, EventData, Settings)
    if Evidence is None:
        if RequestId is not None:
            WaitForCi(RepoName, EventData, Settings, RequestId)
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("ready=false\n")
        return
    PullData = CheckPull(RepoName, Evidence)
    for Revision in (Evidence["head_sha"], Evidence["base_sha"]):
        ProcessTools.run(
            ["git", "fetch", "--no-tags", "origin", str(Revision)],
            check=True,
            timeout=120,
        )
    IsReady = IsContextReady(RepoName, Evidence, PullData, Settings, RequestId)
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write(f"ready={'true' if IsReady else 'false'}\n")


if __name__ == "__main__":
    PrepareRun()
