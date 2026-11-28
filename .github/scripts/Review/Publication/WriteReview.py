from ApiCall import ApiCall
from CheckPull import CheckPull
from ObjectMap import ObjectMap


# native findings and ratings must remain publishable even when external conditions forbid approval
def WriteReview(
    RepoName: str,
    Context: dict[str, object],
    Report: dict[str, object],
    Reviewer: dict[str, object],
    BodyText: str,
    Verdict: str,
) -> None:
    Evidence = ObjectMap(Context["evidence"])
    CheckData = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/check-runs",
            {
                "name": str(ObjectMap(Context["settings"])["CheckName"]),
                "head_sha": Report["head"],
                "external_id": str(Evidence["review_id"]),
                "status": "completed",
                "conclusion": {
                    "APPROVE": "success",
                    "COMMENT": "neutral",
                    "REQUEST_CHANGES": "failure",
                }[Verdict],
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
            {"commit_id": Report["head"], "event": Verdict, "body": BodyText},
        )
    )
    if (
        ObjectMap(ReviewData["user"])["id"] != Reviewer["UserId"]
        or ReviewData["commit_id"] != Report["head"]
    ):
        raise ValueError("Unexpected review identity or revision")
