import json as JsonTools
import os as OsTools
from pathlib import Path
from typing import cast

from Approval.ReadGate import ReadGate
from ObjectMap import ObjectMap
from CheckPull import CheckPull
from Publication.WriteReview import WriteReview
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
    IsClean = (
        Report["complete"]
        and Context["input_complete"]
        and Report["scope_matches"]
        and cast(int, Report["score"]) >= int(str(Settings["MinimumScore"]))
        and not Report["findings"]
    )
    GateInfo = ReadGate(RepoName, Evidence, PullData)
    Verdict = (
        "APPROVE"
        if IsClean and GateInfo["passed"]
        else "COMMENT" if IsClean else "REQUEST_CHANGES"
    )
    Context["approval_gate"] = GateInfo
    Context["settings"] = Settings
    Context["repository_name"] = RepoName
    WriteReview(
        RepoName,
        Context,
        Report,
        Reviewer,
        ReviewBody(Report, Context, Verdict),
        Verdict,
    )


if __name__ == "__main__":
    PublishRun()
