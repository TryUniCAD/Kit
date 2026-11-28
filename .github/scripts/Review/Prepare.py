import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path
from typing import cast

from ObjectMap import ObjectMap
from ReadPages import ReadPages
from CheckPull import CheckPull
from BuildContext import BuildContext
from SelectEvidence import SelectEvidence
from ApiCall import ApiCall


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
            PullNumber = int(str(ObjectMap(EventData["issue"])["number"]))
            PullInfo = ObjectMap(ApiCall(f"repos/{RepoName}/pulls/{PullNumber}"))
            ApiCall(
                f"repos/{RepoName}/check-runs",
                {
                    "name": Settings["CheckName"],
                    "head_sha": ObjectMap(PullInfo["head"])["sha"],
                    "status": "completed",
                    "conclusion": "neutral",
                    "output": {
                        "title": "Mention requires current successful CI",
                        "summary": f"No eligible successful CI evidence was found for this PR.\n\nMention comment: {RequestId}\n\nCI run: unavailable",
                    },
                },
            )
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
    FileList = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/files")
    if len(FileList) != PullData["changed_files"]:
        raise ValueError("Changed file inventory is incomplete")
    try:
        Content = BuildContext(Evidence, PullData, FileList, RequestId)
    except ValueError as ErrorInfo:
        ApiCall(
            f"repos/{RepoName}/check-runs",
            {
                "name": Settings["CheckName"],
                "head_sha": Evidence["head_sha"],
                "external_id": str(Evidence["run_id"]),
                "status": "completed",
                "conclusion": "failure",
                "output": {
                    "title": "Review input exceeds supported bounds",
                    "summary": str(ErrorInfo)
                    + (
                        f"\n\nMention comment: {RequestId}\n\nCI run: {Evidence['run_id']}"
                        if RequestId is not None
                        else ""
                    ),
                },
            },
        )
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("ready=false\n")
        return
    Path("ReviewInput").mkdir()
    Path("ReviewInput/Context.json").write_text(Content)
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write("ready=true\n")


if __name__ == "__main__":
    PrepareRun()
