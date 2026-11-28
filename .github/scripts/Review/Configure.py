import json as JsonTools
import re as RegexTools
import sys as SysTools
from pathlib import Path
from typing import cast

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# verified live identities must replace the former reviewer without guessed bot accounts
def ConfigureApp(AppSlug: str) -> None:
    if not RegexTools.fullmatch(r"[a-z0-9-]+", AppSlug):
        raise ValueError("Invalid app slug")
    ConfigPath = Path(".agents/skills/standard-pr-practice/ReviewBot.json")
    Config = ObjectMap(JsonTools.loads(ConfigPath.read_text()))
    Settings = ObjectMap(Config["AccountReview"])
    AppData = ObjectMap(ApiCall(f"apps/{AppSlug}"))
    BotData = ObjectMap(ApiCall(f"users/{AppSlug}[bot]"))
    if (
        AppData["id"] != Settings["AppId"]
        or ObjectMap(AppData["owner"])["login"] != "TryUniCAD"
        or BotData["type"] != "Bot"
    ):
        raise ValueError("App identity or owner mismatch")
    InstallData = ObjectMap(ApiCall("orgs/TryUniCAD/installations?per_page=100"))
    Installations = cast(list[object], InstallData["installations"])
    Matches = [
        ObjectMap(Entry)
        for Entry in Installations
        if ObjectMap(Entry)["app_id"] == Settings["AppId"]
    ]
    if len(Matches) != 1:
        raise ValueError("Install the app on TryUniCAD before configuring it")
    Permissions = ObjectMap(Matches[0]["permissions"])
    for PermName, Access in {
        "pull_requests": "write",
        "checks": "write",
        "actions": "read",
        "contents": "read",
        "environments": "write",
    }.items():
        if Permissions.get(PermName) != Access:
            raise ValueError(f"App permission must be {PermName}: {Access}")
    Config["Reviewers"] = [
        {
            "Trigger": "schedule",
            "Workflow": Settings["Workflow"],
            "AppId": AppData["id"],
            "AppSlug": AppData["slug"],
            "UserId": BotData["id"],
            "UserLogin": BotData["login"],
            "Checks": [Settings["CheckName"]],
            "Statuses": [],
            "Documentation": "Documentation/Tasks/AccountReviewer.md",
        }
    ]
    Settings["MentionCommands"] = [
        f"@{AppData['slug']}",
        f"@{AppData['slug']} review",
    ]
    Config["AccountReview"] = Settings
    ConfigPath.write_text(JsonTools.dumps(Config, indent=2) + "\n")


if __name__ == "__main__":
    ConfigureApp(SysTools.argv[1])
