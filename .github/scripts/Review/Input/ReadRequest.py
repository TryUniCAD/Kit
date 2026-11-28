import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from CheckPull import CheckPull
from Input.MakeContext import MakeContext
from Input.SelectReview import SelectReview
from ObjectMap import ObjectMap


# request parsing must bind trusted policy and live scope before input preparation or account execution
def ReadRequest(RepoName: str) -> tuple[dict[str, object], dict[str, object]] | None:
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
    Reviewer = ObjectMap(cast(list[object], Config["Reviewers"])[0])
    Settings = {
        **ObjectMap(Config["AccountReview"]),
        "UserId": Reviewer["UserId"],
        "PolicyRevision": OsTools.environ["GITHUB_SHA"],
        "TrustedRequest": OsTools.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch"
        or "comment" in EventData,
    }
    Evidence = SelectReview(RepoName, EventData, Settings)
    if Evidence is None:
        return None
    return (
        MakeContext(Evidence, CheckPull(RepoName, Evidence), Settings, RequestId),
        Settings,
    )
