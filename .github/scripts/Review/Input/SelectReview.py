import os as OsTools

from CheckPull import CheckPull
from HasReport import HasReport
from Input.ReadSnapshot import ReadSnapshot
from ObjectMap import ObjectMap
from ReadEvidence import ReadEvidence
from ReadPages import ReadPages


# every proposed revision needs review discovery independently of successful ci run discovery
def SelectReview(
    RepoName: str, EventData: dict[str, object], Settings: dict[str, object]
) -> dict[str, object] | None:
    Inputs = ObjectMap(EventData.get("inputs", {}))
    TargetPull = (
        ObjectMap(EventData["issue"])["number"]
        if "issue" in EventData
        else Inputs.get("pull")
    )
    if not TargetPull and Inputs.get("id"):
        TargetPull = ReadEvidence(RepoName, int(str(Inputs["id"])))["pull_number"]
    if TargetPull:
        if not str(TargetPull).isdigit() or int(str(TargetPull)) < 1:
            raise ValueError("Invalid requested PR number")
        Evidence = ReadSnapshot(RepoName, int(str(TargetPull)), Settings)
        if "comment" in EventData or Inputs.get("force") == "true" or Inputs.get("id"):
            return Evidence
        return (
            None
            if HasReport(RepoName, Evidence, Settings, CheckPull(RepoName, Evidence))
            else Evidence
        )
    Pulls = ReadPages(f"repos/{RepoName}/pulls?state=open&sort=updated&direction=desc")
    Offset = (
        ((int(OsTools.environ["GITHUB_RUN_NUMBER"]) - 1) * 20) % len(Pulls)
        if Pulls
        else 0
    )
    for Entry in (Pulls + Pulls)[Offset : Offset + min(20, len(Pulls))]:
        try:
            Evidence = ReadSnapshot(RepoName, int(str(Entry["number"])), Settings)
            PullData = CheckPull(RepoName, Evidence)
        except ValueError:
            continue
        if not HasReport(RepoName, Evidence, Settings, PullData):
            return Evidence
    return None
