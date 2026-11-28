import json as JsonTools
import os as OsTools
import sys as SysTools
from pathlib import Path
from typing import cast

from ApiCall import ApiCall
from MentionStatus import MentionStatus
from ObjectMap import ObjectMap
from ReadPages import ReadPages


# collaborators need visible request progress without exposing publishing credentials to the model
def ReactMention(StateName: str) -> None:
    if StateName not in ("started", "complete"):
        raise ValueError("Unexpected review reaction state")
    Context = ObjectMap(JsonTools.loads(Path("ReviewInput/Context.json").read_text()))
    CommentId = Context.get("mention_comment")
    if CommentId is None:
        return
    if type(CommentId) is not int or CommentId < 1:
        raise ValueError("Invalid mention comment identity")
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    UserIdent = ObjectMap(cast(list[object], Config["Reviewers"])[0])["UserId"]
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    Content = (
        "eyes"
        if StateName == "started"
        else (
            MentionStatus(RepoName, Context, UserIdent)
            if OsTools.environ.get("REVIEW_SUCCEEDED") == "true"
            else "confused"
        )
    )
    RouteName = f"repos/{RepoName}/issues/comments/{CommentId}/reactions"
    Reaction = ObjectMap(ApiCall(RouteName, {"content": Content}))
    if ObjectMap(Reaction["user"])["id"] != UserIdent:
        raise ValueError("Unexpected reaction publishing identity")
    if StateName == "started":
        return
    for Entry in ReadPages(RouteName):
        if Entry["content"] == "eyes" and ObjectMap(Entry["user"])["id"] == UserIdent:
            ApiCall(f"{RouteName}/{Entry['id']}", MethodName="DELETE")


if __name__ == "__main__":
    ReactMention(SysTools.argv[1])
