import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
import sys as SysTools
import tempfile as TempTools
from pathlib import Path
from typing import cast

import pytest as Pytest


# the real admission command must reject public comment shapes without accessing protected credentials
@Pytest.mark.parametrize(
    "CaseName",
    (
        "schedule",
        "workflow_dispatch",
        "quoted",
        "issue",
        "bot",
        "edited",
        "unrelated",
        "long",
    ),
)
def CheckMentionCli(CaseName: str) -> None:
    RootPath = Path(__file__).resolve().parents[2]
    Config = cast(
        dict[str, object],
        JsonTools.loads(
            (
                RootPath / ".agents/skills/standard-pr-practice/ReviewBot.json"
            ).read_text()
        ),
    )
    Settings = cast(dict[str, object], Config["AccountReview"])
    Command = cast(list[str], Settings["MentionCommands"])[0]
    Comment: dict[str, object] = {
        "body": Command,
        "user": {"login": "review-user", "id": 1, "type": "User"},
    }
    IssueData: dict[str, object] = {"number": 1, "pull_request": {}}
    EventData: dict[str, object] = {
        "action": "created",
        "comment": Comment,
        "issue": IssueData,
        "sender": {"id": 1},
    }
    if CaseName == "quoted":
        Comment["body"] = "> " + Command
    if CaseName == "issue":
        assert IssueData.pop("pull_request") == {}
    if CaseName == "bot":
        Comment["user"] = {"login": "review-bot", "id": 1, "type": "Bot"}
    if CaseName == "edited":
        EventData["action"] = "edited"
    if CaseName == "unrelated":
        Comment["body"] = "Please inspect this later"
    if CaseName == "long":
        Comment["body"] = Command + " " * 129
    with TempTools.TemporaryDirectory() as TempName:
        TempPath = Path(TempName)
        assert (TempPath / "Event.json").write_text(JsonTools.dumps(EventData)) > 0
        Result = ProcessTools.run(
            [SysTools.executable, str(RootPath / ".github/scripts/Review/Admit.py")],
            cwd=RootPath,
            env={
                **OsTools.environ,
                "GITHUB_EVENT_NAME": (
                    CaseName
                    if CaseName in ("schedule", "workflow_dispatch")
                    else "issue_comment"
                ),
                "GITHUB_EVENT_PATH": str(TempPath / "Event.json"),
                "GITHUB_OUTPUT": str(TempPath / "Output.txt"),
                "GH_TOKEN": "",
                "GITHUB_TOKEN": "",
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert Result.returncode == 0, Result.stderr
        assert (TempPath / "Output.txt").read_text() == (
            "allowed=true\n"
            if CaseName in ("schedule", "workflow_dispatch")
            else "allowed=false\n"
        )
