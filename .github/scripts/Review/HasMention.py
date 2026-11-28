from ObjectMap import ObjectMap
from ReadChecks import ReadChecks


# app attributed receipts prevent repeatedly processing the same request for one head
def HasMention(
    RepoName: str, HeadSha: str, CommentId: object, Settings: dict[str, object]
) -> bool:
    for Check in ReadChecks(RepoName, HeadSha, Settings):
        if (
            ObjectMap(Check["app"])["id"] != Settings["AppId"]
            or Check["name"] != Settings["CheckName"]
        ):
            continue
        Summary = str(ObjectMap(Check["output"]).get("summary", ""))
        if Summary.split("\n\n")[-2:-1] == [f"Mention comment: {CommentId}"]:
            return True
    return False
