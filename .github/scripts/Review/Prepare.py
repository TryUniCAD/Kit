import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path

from ObjectMap import ObjectMap
from ReadPages import ReadPages
from CheckPull import CheckPull
from CollectFiles import CollectFiles, ReadSource
from ReadEvidence import ReadEvidence


# untrusted workflow inputs must be checked before any account credential is restored
def PrepareRun() -> None:
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    EventData = ObjectMap(
        JsonTools.loads(Path(OsTools.environ["GITHUB_EVENT_PATH"]).read_text())
    )
    RunIdent = int(
        str(ObjectMap(EventData.get("workflow_run", EventData.get("inputs")))["id"])
    )
    Evidence = ReadEvidence(RepoName, RunIdent)
    PullData = CheckPull(RepoName, Evidence)
    for Revision in (Evidence["head_sha"], Evidence["base_sha"]):
        ProcessTools.run(
            ["git", "fetch", "--no-tags", "origin", str(Revision)],
            check=True,
            timeout=120,
        )
    FileList = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/files")
    if len(FileList) != PullData["changed_files"]:
        raise ValueError("Changed file inventory is incomplete")
    Context = {
        "evidence": Evidence,
        "title": PullData["title"],
        "body": PullData["body"],
        "files": CollectFiles(FileList, Evidence),
        "policy": {
            FileName: ReadSource(str(Evidence["base_sha"]), FileName)
            for FileName in (
                "AGENTS.md",
                "Roadmap.md",
                ".agents/skills/standard-pr-practice/SKILL.md",
                "Documentation/Planning/Generated/Tasks.md",
                "Documentation/Planning/Generated/Deliveries.md",
                "Documentation/Reference/Operations/CadSuccessCriteria.md",
            )
        },
    }
    Content = JsonTools.dumps(Context)
    if len(Content.encode()) > 900000:
        raise ValueError("PR exceeds the complete review context limit")
    Path("ReviewInput").mkdir()
    Path("ReviewInput/Context.json").write_text(Content)


if __name__ == "__main__":
    PrepareRun()
