from ObjectMap import ObjectMap
from ReadChecks import GetCheckId, ReadChecks
from ReadPages import ReadPages


# successful publication needs both a native report and the actual approving review
def HasReport(
    RepoName: str,
    Evidence: dict[str, object],
    Settings: dict[str, object],
    PullData: dict[str, object],
) -> bool:
    Matches = [
        Entry
        for Entry in ReadChecks(RepoName, str(Evidence["head_sha"]), Settings)
        if ObjectMap(Entry)["name"] == Settings["CheckName"]
        and ObjectMap(ObjectMap(Entry)["app"])["id"] == Settings["AppId"]
        and ObjectMap(Entry).get("external_id") == str(Evidence["review_id"])
        and ObjectMap(Entry)["status"] == "completed"
    ]
    if not Matches:
        return False
    Latest = max(Matches, key=GetCheckId)
    if Latest["conclusion"] == "neutral":
        return not ReadGate(RepoName, Evidence, PullData)["passed"]
    if Latest["conclusion"] != "success":
        return True
    Reviews = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/reviews")
    return any(
        Entry["commit_id"] == Evidence["head_sha"]
        and Entry["state"] == "APPROVED"
        and ObjectMap(Entry["user"])["id"] == Settings["UserId"]
        and str(Entry["body"]).endswith(f"\n\nReview snapshot: {Evidence['review_id']}")
        for Entry in Reviews
    )


from Approval.ReadGate import ReadGate
