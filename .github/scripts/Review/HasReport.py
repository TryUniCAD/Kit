from ObjectMap import ObjectMap
from ReadChecks import ReadChecks
from ReadPages import ReadPages


# successful publication needs both a native report and the actual approving review
def HasReport(
    RepoName: str, Evidence: dict[str, object], Settings: dict[str, object]
) -> bool:
    Matches = [
        Entry
        for Entry in ReadChecks(RepoName, str(Evidence["head_sha"]), Settings)
        if ObjectMap(Entry)["name"] == Settings["CheckName"]
        and ObjectMap(ObjectMap(Entry)["app"])["id"] == Settings["AppId"]
        and ObjectMap(Entry).get("external_id") == str(Evidence["run_id"])
        and ObjectMap(Entry)["status"] == "completed"
    ]
    if not Matches:
        return False
    if Matches[0]["conclusion"] != "success":
        return True
    Reviews = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/reviews")
    return any(
        Entry["commit_id"] == Evidence["head_sha"]
        and Entry["state"] == "APPROVED"
        and ObjectMap(Entry["user"])["id"] == Settings["UserId"]
        and str(Entry["body"]).endswith(f"\n\nCI run: {Evidence['run_id']}")
        for Entry in Reviews
    )
