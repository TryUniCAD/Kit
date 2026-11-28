from pathlib import Path

from tests.Policy.ContextBudget.GitCommand import GitCommand


# real patches and independently committed target data reproduce the collector production input
def MakeInput(
    RootPath: Path,
    BeforeSha: str,
    HeadValue: str,
    TargetSha: str,
    FileNames: tuple[str, ...],
) -> dict[str, object]:
    FileList: list[dict[str, object]] = []
    for FileName in FileNames:
        PatchText = GitCommand(
            RootPath, "diff", "--no-ext-diff", BeforeSha, HeadValue, "--", FileName
        )
        FileList.append(
            {"filename": FileName, "status": "modified", "patch": PatchText}
        )
    return {
        "Evidence": {
            "merge_base_sha": BeforeSha,
            "head_sha": HeadValue,
            "base_sha": TargetSha,
        },
        "PullData": {
            "changed_files": len(FileNames),
            "title": "Context process compatibility",
            "body": "Real git sources only",
        },
        "FileList": FileList,
        "Settings": {
            "Model": "fixture-no-model",
            "ReasoningEffort": "low",
            "PolicyRevision": BeforeSha,
        },
    }
