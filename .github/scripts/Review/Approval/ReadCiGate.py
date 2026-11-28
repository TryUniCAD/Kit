import re as RegexTools
import subprocess as ProcessTools
from typing import cast

from ApiCall import ApiCall
from Approval.HasCiComplete import HasCiComplete
from ObjectMap import ObjectMap
from ReadEvidence import ReadEvidence
from ReadChecks import GetCheckId


# only the latest trusted aggregate with matching immutable evidence may unlock app approval
def ReadCiGate(RepoName: str, Evidence: dict[str, object]) -> dict[str, object]:
    CheckData = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/commits/{Evidence['head_sha']}/check-runs?check_name=CI%20Agg&app_id=15368&filter=all&per_page=100"
        )
    )
    Checks = [ObjectMap(Entry) for Entry in cast(list[object], CheckData["check_runs"])]
    if not Checks:
        return {"passed": False, "reason": "CI aggregate is unavailable"}
    Latest = max(Checks, key=GetCheckId)
    if Latest["status"] != "completed" or Latest["conclusion"] != "success":
        return {"passed": False, "reason": "CI is pending or unsuccessful"}
    if not HasCiComplete(RepoName, str(Evidence["head_sha"])):
        return {
            "passed": False,
            "reason": "Other CI checks are pending or unsuccessful",
        }
    RunMatch = RegexTools.fullmatch(
        rf"https://github\.com/{RegexTools.escape(RepoName)}/actions/runs/([0-9]+)/job/[0-9]+",
        str(Latest.get("details_url", "")),
        flags=RegexTools.IGNORECASE,
    )
    if RunMatch is None:
        return {"passed": False, "reason": "CI provenance is unavailable"}
    try:
        CiProof = ReadEvidence(RepoName, int(RunMatch.group(1)))
    except (ValueError, ProcessTools.CalledProcessError):
        return {"passed": False, "reason": "CI evidence is unavailable"}
    if any(
        CiProof[Field] != Evidence[Field]
        for Field in ("pull_number", "repository_id", "head_sha", "base_sha")
    ):
        return {"passed": False, "reason": "CI evidence is stale"}
    return {"passed": True, "reason": "Current CI passed", "run_id": CiProof["run_id"]}
