import io as IoTools
import json as JsonTools
import subprocess as ProcessTools
from typing import cast
from zipfile import ZipFile

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# approvals require the existing aggregate evidence for the exact successful workflow attempt
def ReadEvidence(RepoName: str, RunIdent: int) -> dict[str, object]:
    RunData = ObjectMap(ApiCall(f"repos/{RepoName}/actions/runs/{RunIdent}"))
    if (
        RunData["event"] != "pull_request_target"
        or RunData["path"] != ".github/workflows/PullRequest.yml"
        or RunData["status"] != "completed"
        or RunData["conclusion"] != "success"
        or ObjectMap(RunData["repository"])["full_name"] != RepoName
    ):
        raise ValueError("Review requires successful trusted PR CI")
    ArtifactData = ObjectMap(
        ApiCall(f"repos/{RepoName}/actions/runs/{RunIdent}/artifacts?per_page=100")
    )
    Artifacts = cast(list[object], ArtifactData["artifacts"])
    Matches = [
        ObjectMap(Entry)
        for Entry in Artifacts
        if ObjectMap(Entry)["name"] == f"PrCiEvidence-{RunData['run_attempt']}"
        and not ObjectMap(Entry)["expired"]
    ]
    if len(Matches) != 1 or int(str(Matches[0]["size_in_bytes"])) > 65536:
        raise ValueError("Missing or oversized CI evidence")
    Download = ProcessTools.run(
        [
            "gh",
            "api",
            f"repos/{RepoName}/actions/artifacts/{Matches[0]['id']}/zip",
            "--hostname",
            "github.com",
        ],
        capture_output=True,
        check=True,
        timeout=60,
    )
    with ZipFile(IoTools.BytesIO(Download.stdout)) as Archive:
        EntryInfo = Archive.getinfo("Evidence.json")
        if EntryInfo.file_size > 16384:
            raise ValueError("CI evidence is too large")
        Evidence = ObjectMap(JsonTools.loads(Archive.read(EntryInfo)))
    if (
        Evidence["run_id"] != RunIdent
        or Evidence["run_attempt"] != RunData["run_attempt"]
    ):
        raise ValueError("CI evidence attempt mismatch")
    return Evidence
