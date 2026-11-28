import subprocess as ProcessTools

from ObjectMap import ObjectMap
from Planning.BuildProof import BuildProof


# exact derivation proof must replace omissions only for supported outputs on the current trusted base
def PlanCoverage(
    Evidence: dict[str, object],
    Settings: dict[str, object],
    Sources: list[dict[str, object]],
) -> dict[str, object] | None:
    Revision = str(Settings["PolicyRevision"])
    if any(
        len(CommitSha) != 40
        or any(Letter not in "0123456789abcdef" for Letter in CommitSha)
        for CommitSha in (Revision, str(Evidence["head_sha"]))
    ):
        return None
    if Evidence["base_sha"] != Revision or Evidence["merge_base_sha"] != Revision:
        return None
    FileNames = [
        str(Source["path"])
        for Source in Sources
        if Source["path"]
        in (
            "Documentation/Planning/Generated/BoardData.json",
            "Documentation/Planning/Generated/BoardData.js",
        )
        and Source["status"] == "modified"
        and "omitted" in Source
    ]
    if not FileNames:
        return None
    try:
        ProofData = BuildProof(Revision, str(Evidence["head_sha"]), Sources, FileNames)
    except (ValueError, OSError, ProcessTools.SubprocessError):
        return None
    Receipts = ObjectMap(ProofData["files"])
    for Source in Sources:
        FileName = str(Source["path"])
        if FileName not in Receipts:
            continue
        Source.clear()
        Source.update(
            {
                "path": FileName,
                "status": "modified",
                "verified_generated": Receipts[FileName],
            }
        )
    return ProofData
