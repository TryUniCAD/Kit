import json as JsonTools
import os as OsTools
from pathlib import Path

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# failed runtime jobs need a native result instead of leaving contributors waiting for an absent review
def FailReview() -> None:
    Context = ObjectMap(JsonTools.loads(Path("ReviewInput/Context.json").read_text()))
    Evidence = ObjectMap(Context["evidence"])
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Settings = ObjectMap(Config["AccountReview"])
    Summary = (
        "The review workflow did not complete successfully. This failed report must be resolved before readiness.\n\n"
        f"[Workflow log](https://github.com/{OsTools.environ['GITHUB_REPOSITORY']}/actions/runs/{OsTools.environ['GITHUB_RUN_ID']})"
    )
    if Context.get("mention_comment") is not None:
        Summary += f"\n\nMention comment: {Context['mention_comment']}"
    Summary += f"\n\nReview snapshot: {Evidence['review_id']}"
    CheckData = ObjectMap(
        ApiCall(
            f"repos/{OsTools.environ['GITHUB_REPOSITORY']}/check-runs",
            {
                "name": Settings["CheckName"],
                "head_sha": Evidence["head_sha"],
                "external_id": str(Evidence["review_id"]),
                "status": "completed",
                "conclusion": "failure",
                "output": {"title": "Review workflow failed", "summary": Summary},
            },
        )
    )
    if ObjectMap(CheckData["app"])["id"] != Settings["AppId"]:
        raise ValueError("Unexpected failure report identity")


if __name__ == "__main__":
    FailReview()
