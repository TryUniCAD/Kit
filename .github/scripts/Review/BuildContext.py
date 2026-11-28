import json as JsonTools

from CollectFiles import CollectFiles, ReadSource


# unreviewable source sizes must fail before any account credential reaches the runner
def BuildContext(
    Evidence: dict[str, object],
    PullData: dict[str, object],
    FileList: list[dict[str, object]],
    RequestId: int | None = None,
) -> str:
    Context = {
        "evidence": Evidence,
        "title": PullData["title"],
        "body": PullData["body"],
        "mention_comment": RequestId,
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
    return Content
