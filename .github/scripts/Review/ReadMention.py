from ApiCall import ApiCall
from CanComment import CanComment
from HasMention import HasMention
from ObjectMap import ObjectMap


# polled public records need live admission before their data can select a protected review
def ReadMention(
    RepoName: str, Comment: dict[str, object], Settings: dict[str, object]
) -> dict[str, object] | None:
    IssueUrl = str(Comment["issue_url"])
    Prefix = f"https://api.github.com/repos/{RepoName}/issues/"
    if not IssueUrl.startswith(Prefix) or not IssueUrl[len(Prefix) :].isdigit():
        raise ValueError("Unexpected mention issue URL")
    PullNumber = int(IssueUrl[len(Prefix) :])
    IssueData = ObjectMap(ApiCall(f"repos/{RepoName}/issues/{PullNumber}"))
    if IssueData["state"] != "open" or "pull_request" not in IssueData:
        return None
    Commenter = ObjectMap(Comment["user"])
    EventData = {
        "action": "created",
        "comment": {
            "id": Comment["id"],
            "body": Comment["body"],
            "user": {
                "id": Commenter["id"],
                "login": Commenter["login"],
                "type": Commenter["type"],
            },
        },
        "issue": {"number": PullNumber, "pull_request": {}},
        "sender": {"id": Commenter["id"]},
    }
    if not CanComment(RepoName, EventData, Settings):
        return None
    PullData = ObjectMap(ApiCall(f"repos/{RepoName}/pulls/{PullNumber}"))
    HeadData = ObjectMap(PullData["head"])
    if PullData["draft"] or ObjectMap(HeadData["repo"])["full_name"] != RepoName:
        return None
    if HasMention(RepoName, str(HeadData["sha"]), Comment["id"], Settings):
        return None
    return EventData
