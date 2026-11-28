import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from ApiCall import ApiCall
from IsCommand import IsCommand
from ObjectMap import ObjectMap
from ReadMention import ReadMention


# scheduled recovery and explicit comment dispatch need the same live authorization boundary
def SelectMention(
    RepoName: str, Settings: dict[str, object]
) -> dict[str, object] | None:
    EventName = OsTools.environ["GITHUB_EVENT_NAME"]
    Inputs = ObjectMap(
        ObjectMap(
            JsonTools.loads(Path(OsTools.environ["GITHUB_EVENT_PATH"]).read_text())
        ).get("inputs", {})
    )
    CommentId = Inputs.get("comment") if EventName == "workflow_dispatch" else None
    if CommentId:
        if not str(CommentId).isdigit() or int(str(CommentId)) < 1:
            raise ValueError("Invalid requested comment identity")
        Comments = [ApiCall(f"repos/{RepoName}/issues/comments/{CommentId}")]
    elif EventName == "schedule" or EventName == "push":
        Comments = cast(
            list[object],
            ApiCall(
                f"repos/{RepoName}/issues/comments?sort=created&direction=desc&per_page=100"
            ),
        )
    else:
        return None
    Candidates = [
        ObjectMap(Entry)
        for Entry in Comments
        if IsCommand(ObjectMap(Entry).get("body"), Settings)
        and ObjectMap(Entry)["created_at"] == ObjectMap(Entry)["updated_at"]
        and ObjectMap(ObjectMap(Entry)["user"]).get("type") == "User"
    ]
    Offset = (
        ((int(OsTools.environ["GITHUB_RUN_NUMBER"]) - 1) * 10) % len(Candidates)
        if Candidates
        else 0
    )
    for Comment in (Candidates + Candidates)[
        Offset : Offset + min(10, len(Candidates))
    ]:
        Request = ReadMention(RepoName, Comment, Settings)
        if Request is not None:
            return Request
    if CommentId:
        raise ValueError("Requested comment is unauthorized invalid or already handled")
    return None
