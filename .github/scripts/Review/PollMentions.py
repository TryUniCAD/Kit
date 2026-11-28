import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from ApiCall import ApiCall
from IsCommand import IsCommand
from ObjectMap import ObjectMap
from ReadMention import ReadMention


# trusted polling admits mentions without exposing privileged workflows to public comment events
def PollMentions() -> None:
    if OsTools.environ["GITHUB_EVENT_NAME"] != "schedule":
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("mention=false\n")
        return
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Settings = ObjectMap(Config["AccountReview"])
    Comments = cast(
        list[object],
        ApiCall(
            f"repos/{RepoName}/issues/comments?sort=created&direction=desc&per_page=100"
        ),
    )
    Candidates = [
        ObjectMap(Entry)
        for Entry in Comments
        if IsCommand(ObjectMap(Entry).get("body"), Settings)
        and ObjectMap(Entry)["created_at"] == ObjectMap(Entry)["updated_at"]
        and ObjectMap(ObjectMap(Entry)["user"]).get("type") == "User"
    ]
    StartIndex = (
        ((int(OsTools.environ["GITHUB_RUN_NUMBER"]) - 1) * 10) % len(Candidates)
        if Candidates
        else 0
    )
    for Comment in (Candidates + Candidates)[
        StartIndex : StartIndex + min(10, len(Candidates))
    ]:
        EventData = ReadMention(RepoName, Comment, Settings)
        if EventData is None:
            continue
        Path("ReviewRequest").mkdir()
        Path("ReviewRequest/Event.json").write_text(JsonTools.dumps(EventData))
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("mention=true\n")
        return
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write("mention=false\n")


if __name__ == "__main__":
    PollMentions()
