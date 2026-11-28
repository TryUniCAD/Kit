import hashlib as HashTools
import os as OsTools
import subprocess as ProcessTools
import sys as SysTools
from pathlib import Path
from tempfile import TemporaryDirectory

from ObjectMap import ObjectMap
from Planning.ReadBlob import ReadBlob
from Planning.StagePlan import StagePlan


# trusted regeneration covers large derived files only when every proposed input remains visible to review
def BuildProof(
    Revision: str,
    HeadSha: str,
    Sources: list[dict[str, object]],
    FileNames: list[str],
) -> dict[str, object]:
    ChangedInputs = {
        str(Source["path"]): Source
        for Source in Sources
        if Source["path"]
        in (
            "Documentation/Planning/Links.json",
            "Documentation/Planning/PullRequests.json",
        )
    }
    if any("omitted" in Source for Source in ChangedInputs.values()):
        raise ValueError("Planning inputs lack full review coverage")
    with TemporaryDirectory(prefix="KitReviewPlanning") as WorkDir:
        RootPath = Path(WorkDir)
        StagePlan(RootPath, Revision, HeadSha, ChangedInputs)
        Receipts: dict[str, object] = {}
        for PhaseName in ("before", "after"):
            if PhaseName == "after":
                for FileName, Source in ChangedInputs.items():
                    (RootPath / FileName).write_bytes(str(Source["after"]).encode())
            ProcessTools.run(
                [
                    SysTools.executable,
                    str(RootPath / "re/automation/Planning/Build.py"),
                    "--root",
                    WorkDir,
                ],
                cwd=WorkDir,
                env={
                    "PATH": OsTools.defpath,
                    "LANG": "C.UTF-8",
                    "TZ": "UTC",
                    "SYSTEMROOT": OsTools.environ.get("SYSTEMROOT", ""),
                },
                capture_output=True,
                check=True,
                timeout=60,
            )
            for FileName in FileNames:
                Content = (RootPath / FileName).read_bytes()
                if Content != ReadBlob(
                    Revision if PhaseName == "before" else HeadSha, FileName
                ):
                    raise ValueError(
                        "Generated planning bytes differ from trusted rebuild"
                    )
                Receipt = ObjectMap(Receipts.setdefault(FileName, {}))
                Receipt[PhaseName] = {
                    "sha256": HashTools.sha256(Content).hexdigest(),
                    "bytes": len(Content),
                }
    return {
        "generator_revision": Revision,
        "reviewed_inputs": sorted(ChangedInputs),
        "files": Receipts,
    }
