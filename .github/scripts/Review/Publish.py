import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from ApiCall import ApiCall
from ObjectMap import ObjectMap
from CheckPull import CheckPull
from ReadEvidence import ReadEvidence
from Validate import ValidateReport
from ReviewBody import ReviewBody


# publishing must recheck live scope ci and identity outside the model runtime
def PublishRun() -> None:
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    Context = ObjectMap(JsonTools.loads(Path("ReviewInput/Context.json").read_text()))
    Report = ValidateReport(
        JsonTools.loads(Path("ReviewOutput/Report.json").read_text()), Context
    )
    Evidence = ObjectMap(Context["evidence"])
    if ReadEvidence(RepoName, int(str(Evidence["run_id"]))) != Evidence:
        raise ValueError("CI evidence changed during review")
    PullData = CheckPull(RepoName, Evidence)
    if (PullData["title"], PullData["body"]) != (Context["title"], Context["body"]):
        raise ValueError("PR description changed during review")
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Reviewers = cast(list[object], Config["Reviewers"])
    Matches = [
        ObjectMap(Entry)
        for Entry in Reviewers
        if ObjectMap(Entry)["AppId"] == int(OsTools.environ["REVIEW_APP_ID"])
    ]
    if len(Matches) != 1:
        raise ValueError(
            "Installed app must be registered in ReviewBot.json before activation"
        )
    Reviewer = Matches[0]
    Settings = ObjectMap(Config["AccountReview"])
    IsApproved = (
        Report["complete"]
        and Report["scope_matches"]
        and cast(int, Report["score"]) >= int(str(Settings["MinimumScore"]))
        and not Report["findings"]
    )
    Verdict = "APPROVE" if IsApproved else "REQUEST_CHANGES"
    BodyText = ReviewBody(Report)
    if Context.get("mention_comment") is not None:
        BodyText += f"\n\nMention comment: {Context['mention_comment']}"
    BodyText += f"\n\nCI run: {Evidence['run_id']}"
    CheckName = cast(list[str], Reviewer["Checks"])[0]
    CheckData = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/check-runs",
            {
                "name": CheckName,
                "head_sha": Report["head"],
                "external_id": str(Evidence["run_id"]),
                "status": "completed",
                "conclusion": "success" if IsApproved else "failure",
                "output": {
                    "title": f"Soundness {Report['score']}/5",
                    "summary": BodyText,
                },
            },
        )
    )
    if ObjectMap(CheckData["app"])["id"] != Reviewer["AppId"]:
        raise ValueError("Unexpected publishing app identity")
    CheckPull(RepoName, Evidence)
    ReviewData = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/pulls/{Evidence['pull_number']}/reviews",
            {
                "commit_id": Report["head"],
                "event": Verdict,
                "body": BodyText,
            },
        )
    )
    if (
        ObjectMap(ReviewData["user"])["id"] != Reviewer["UserId"]
        or ReviewData["commit_id"] != Report["head"]
    ):
        raise ValueError("Unexpected review identity or revision")


if __name__ == "__main__":
    PublishRun()
