import re as RegexTools

from ApiCall import ApiCall
from IsMention import IsMention
from ObjectMap import ObjectMap


# command authors need current write access independently of the pull request author
def CanComment(
    RepoName: str, EventData: dict[str, object], Settings: dict[str, object]
) -> bool:
    if not IsMention(EventData, Settings):
        return False
    Commenter = ObjectMap(ObjectMap(EventData["comment"])["user"])
    LoginName = str(Commenter["login"])
    if not RegexTools.fullmatch(r"[A-Za-z0-9-]{1,39}", LoginName):
        raise ValueError("Invalid commenter identity")
    if ObjectMap(EventData["sender"])["id"] != Commenter["id"]:
        raise ValueError("Comment sender identity mismatch")
    Permission = ObjectMap(
        ApiCall(f"repos/{RepoName}/collaborators/{LoginName}/permission")
    )
    return Permission["permission"] in ("write", "maintain", "admin")
