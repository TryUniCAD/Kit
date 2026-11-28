import subprocess as ProcessTools

from Approval.ReadCiGate import ReadCiGate


# review publication is useful before readiness but approving requires every external gate to pass
def ReadGate(
    RepoName: str, Evidence: dict[str, object], PullData: dict[str, object]
) -> dict[str, object]:
    if PullData["draft"]:
        return {"passed": False, "reason": "PR is a draft"}
    if PullData.get("mergeable") is not True:
        return {
            "passed": False,
            "reason": "PR has conflicts or mergeability is pending",
        }
    try:
        return ReadCiGate(RepoName, Evidence)
    except (ValueError, ProcessTools.CalledProcessError):
        return {"passed": False, "reason": "CI readiness could not be verified"}
