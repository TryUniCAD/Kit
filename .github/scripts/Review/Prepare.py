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
    EventData = ObjectMap(
        JsonTools.loads(Path(OsTools.environ["GITHUB_EVENT_PATH"]).read_text())
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
        Content = BuildContext(Evidence, PullData, FileList)
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
                    "summary": str(ErrorInfo),
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
