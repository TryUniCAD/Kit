import json as JsonTools

from ReviewSources import ReviewSources
from Input.MakeContext import MakeContext
from Input.ReadSource import ReadSource


# bounded source coverage must remain explicit so incomplete input can never receive automatic approval
def BuildContext(
    Evidence: dict[str, object],
    PullData: dict[str, object],
    FileList: list[dict[str, object]],
    Settings: dict[str, object],
    RequestId: int | None = None,
) -> str:
    Context = MakeContext(Evidence, PullData, Settings, RequestId)
    Context["policy"] = {
        FileName: ReadSource(str(Settings["PolicyRevision"]), FileName)
        for FileName in (
            "AGENTS.md",
            "Roadmap.md",
            ".agents/skills/standard-pr-practice/SKILL.md",
            "Documentation/Planning/Generated/Tasks.md",
            "Documentation/Planning/Generated/Deliveries.md",
            "Documentation/Reference/Operations/CadSuccessCriteria.md",
        )
    }
    Sources: list[dict[str, object]] = []
    Context["files"] = Sources
    for Source in ReviewSources(FileList, Evidence):
        Sources.append(Source)
        if len(JsonTools.dumps(Context).encode()) > 900000:
            Source.update(
                {
                    "before": None,
                    "after": None,
                    "target": None,
                    "patch": None,
                    "omitted": "Complete source exceeds the review context budget",
                }
            )
    Context["omitted_file_count"] = int(str(Context["changed_file_count"])) - len(
        Sources
    )
    Context["input_complete"] = Context["omitted_file_count"] == 0 and not any(
        "omitted" in Source for Source in Sources
    )
    return JsonTools.dumps(Context)
