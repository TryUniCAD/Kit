from typing import cast

from ApiCall import ApiCall
from ObjectMap import ObjectMap
from ReadPages import ReadPages


# successful publication needs both a native report and the actual approving review
def HasReport(
    RepoName: str, Evidence: dict[str, object], Settings: dict[str, object]
) -> bool:
    Checks = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/commits/{Evidence['head_sha']}/check-runs?per_page=100"
        )
    )
    Matches = [
        ObjectMap(Entry)
        for Entry in cast(list[object], Checks["check_runs"])
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
