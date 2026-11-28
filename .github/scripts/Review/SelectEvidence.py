from typing import cast

from ApiCall import ApiCall
from CheckPull import CheckPull
from HasReport import HasReport
from ObjectMap import ObjectMap
from ReadEvidence import ReadEvidence


# scheduled selection keeps privileged workflow execution independent of untrusted completion events
def SelectEvidence(
    RepoName: str, EventData: dict[str, object], Settings: dict[str, object]
) -> dict[str, object] | None:
    if "inputs" in EventData:
        return ReadEvidence(RepoName, int(str(ObjectMap(EventData["inputs"])["id"])))
    TargetPull = (
        ObjectMap(EventData["issue"])["number"] if "issue" in EventData else None
    )
    if TargetPull is not None and (type(TargetPull) is not int or TargetPull < 1):
        raise ValueError("Invalid mention PR number")
    RunList = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/actions/workflows/PullRequest.yml/runs?event=pull_request_target&status=success&per_page={100 if TargetPull is not None else 30}"
        )
    )
    for Entry in cast(list[object], RunList["workflow_runs"]):
        try:
            Evidence = ReadEvidence(RepoName, int(str(ObjectMap(Entry)["id"])))
            if TargetPull is not None and Evidence["pull_number"] != TargetPull:
                continue
            CheckPull(RepoName, Evidence)
        except ValueError:
            continue
        if TargetPull is not None or not HasReport(RepoName, Evidence, Settings):
            return Evidence
    return None
