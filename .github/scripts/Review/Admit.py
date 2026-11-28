import json as JsonTools
import os as OsTools
import re as RegexTools
from pathlib import Path

from ApiCall import ApiCall
from IsMention import IsMention
from ObjectMap import ObjectMap


# public comment admission must complete with read only credentials before protected jobs can start
def AdmitRun() -> None:
    EventName = OsTools.environ["GITHUB_EVENT_NAME"]
    EventData = ObjectMap(
        JsonTools.loads(Path(OsTools.environ["GITHUB_EVENT_PATH"]).read_text())
    )
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    IsAllowed = EventName in ("schedule", "workflow_dispatch")
    if EventName == "issue_comment" and IsMention(
        EventData, ObjectMap(Config["AccountReview"])
    ):
        Commenter = ObjectMap(ObjectMap(EventData["comment"])["user"])
        LoginName = str(Commenter["login"])
        if not RegexTools.fullmatch(r"[A-Za-z0-9-]{1,39}", LoginName):
            raise ValueError("Invalid commenter identity")
        if ObjectMap(EventData["sender"])["id"] != Commenter["id"]:
            raise ValueError("Comment sender identity mismatch")
        RepoName = OsTools.environ["GITHUB_REPOSITORY"]
        Permission = ObjectMap(
            ApiCall(f"repos/{RepoName}/collaborators/{LoginName}/permission")
        )
        IsAllowed = Permission["permission"] in ("write", "maintain", "admin")
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write(f"allowed={'true' if IsAllowed else 'false'}\n")


if __name__ == "__main__":
    AdmitRun()
