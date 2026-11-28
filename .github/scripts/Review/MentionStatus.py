from ObjectMap import ObjectMap
from ReadPages import ReadPages


# completion reactions must reflect a verified native review rather than untrusted model output
def MentionStatus(RepoName: str, Context: dict[str, object], UserIdent: object) -> str:
    Evidence = ObjectMap(Context["evidence"])
    Reviews = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/reviews")
    for Review in reversed(Reviews):
        if (
            Review["commit_id"] == Evidence["head_sha"]
            and ObjectMap(Review["user"])["id"] == UserIdent
            and str(Review["body"]).endswith(
                f"\n\nMention comment: {Context['mention_comment']}\n\nReview snapshot: {Evidence['review_id']}"
            )
        ):
            return {
                "APPROVED": "+1",
                "CHANGES_REQUESTED": "-1",
                "COMMENTED": "hooray",
            }.get(str(Review["state"]), "confused")
    return "confused"
