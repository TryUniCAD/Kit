from typing import cast

from ObjectMap import ObjectMap


# quoted text and unrelated public comments must not authorize credential access
def IsMention(EventData: dict[str, object], Settings: dict[str, object]) -> bool:
    if (
        EventData.get("action") != "created"
        or "comment" not in EventData
        or "issue" not in EventData
    ):
        return False
    IssueData = ObjectMap(EventData["issue"])
    Comment = ObjectMap(EventData["comment"])
    if (
        "pull_request" not in IssueData
        or ObjectMap(Comment["user"]).get("type") != "User"
    ):
        return False
    BodyText = Comment.get("body")
    return (
        isinstance(BodyText, str)
        and len(BodyText) <= 128
        and BodyText.strip().casefold()
        in {
            Command.casefold()
            for Command in cast(list[str], Settings["MentionCommands"])
        }
    )
