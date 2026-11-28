import json as JsonTools
import sys as SysTools
from pathlib import Path

from ReviewSources import ReviewSources
from Input.MakeContext import MakeContext
from Input.ReadSource import ReadSource
from Planning.PlanCoverage import PlanCoverage


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
    ProofData = PlanCoverage(Evidence, Settings, Sources)
    if ProofData is not None:
        Context["generated_verification"] = ProofData
    Context["omitted_file_count"] = int(str(Context["changed_file_count"])) - len(
        Sources
    )
    Context["input_complete"] = Context["omitted_file_count"] == 0 and not any(
        "omitted" in Source for Source in Sources
    )
    Content = JsonTools.dumps(Context)
    if len(Content.encode()) > 900000:
        raise ValueError("Review context exceeds the encoded input budget")
    return Content


if __name__ == "__main__":
    print(BuildContext(**JsonTools.loads(Path(SysTools.argv[1]).read_text())))
