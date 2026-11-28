import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path
from typing import cast

from CheckPull import CheckPull
from Input.ReadMergeBase import ReadMergeBase
from Input.ReadRequest import ReadRequest
from IsContextReady import IsContextReady
from ObjectMap import ObjectMap


# failed preparation still needs revision metadata so native failure reports and reactions can complete
def PrepareRun() -> None:
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    Request = ReadRequest(RepoName)
    if Request is None:
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("selected=false\nready=false\n")
        return
    Context, Settings = Request
    Evidence = ObjectMap(Context["evidence"])
    Path("ReviewInput").mkdir()
    Path("ReviewInput/Context.json").write_text(JsonTools.dumps(Context))
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write("selected=true\nready=false\n")
    Evidence["merge_base_sha"] = ReadMergeBase(RepoName, Evidence)
    for Revision in (
        Evidence["head_sha"],
        Evidence["base_sha"],
        Evidence["merge_base_sha"],
    ):
        ProcessTools.run(
            ["git", "fetch", "--no-tags", "origin", str(Revision)],
            check=True,
            timeout=120,
        )
    IsReady = IsContextReady(
        RepoName,
        Evidence,
        CheckPull(RepoName, Evidence),
        Settings,
        cast(int | None, Context["mention_comment"]),
    )
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write(f"ready={'true' if IsReady else 'false'}\n")


if __name__ == "__main__":
    PrepareRun()
