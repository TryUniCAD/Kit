import json as JsonTools
import os as OsTools
from pathlib import Path

from CanComment import CanComment
from ObjectMap import ObjectMap


# public comment admission must complete with read only credentials before protected jobs can start
def AdmitRun() -> None:
    EventName = OsTools.environ.get(
        "REVIEW_EVENT_NAME", OsTools.environ["GITHUB_EVENT_NAME"]
    )
    EventData = ObjectMap(
        JsonTools.loads(
            Path(
                OsTools.environ.get(
                    "REVIEW_EVENT_PATH", OsTools.environ["GITHUB_EVENT_PATH"]
                )
            ).read_text()
        )
    )
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    IsAllowed = EventName in ("schedule", "workflow_dispatch")
    if EventName == "issue_comment":
        IsAllowed = CanComment(
            OsTools.environ.get("GITHUB_REPOSITORY", ""),
            EventData,
            ObjectMap(Config["AccountReview"]),
        )
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write(f"allowed={'true' if IsAllowed else 'false'}\n")


if __name__ == "__main__":
    AdmitRun()
