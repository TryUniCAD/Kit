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
    Runs = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/actions/workflows/PullRequest.yml/runs?event=pull_request_target&status=success&per_page=30"
        )
    )
    for Entry in cast(list[object], Runs["workflow_runs"]):
        try:
            Evidence = ReadEvidence(RepoName, int(str(ObjectMap(Entry)["id"])))
            CheckPull(RepoName, Evidence)
        except ValueError:
            continue
        if not HasReport(RepoName, Evidence, Settings):
            return Evidence
    return None
