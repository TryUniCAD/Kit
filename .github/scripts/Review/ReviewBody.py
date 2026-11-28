from ObjectMap import ObjectMap
from Publication.FormatEvidence import FormatEvidence
from Publication.FormatFindings import FormatFindings
from Publication.SafeText import SafeText


# every reported issue remains visible even when it cannot be attached to a changed diff line
def ReviewBody(
    Report: dict[str, object], Context: dict[str, object], Verdict: str
) -> str:
    VerdictText = {
        "APPROVE": "Approved",
        "COMMENT": "Reviewed; approval pending",
        "REQUEST_CHANGES": "Changes requested",
    }[Verdict]
    Coverage = (
        "complete" if Report["complete"] and Context["input_complete"] else "incomplete"
    )
    Sections = [
        f"## {VerdictText}",
        f"**Soundness: {Report['score']}/5** · Coverage: **{Coverage}**",
        SafeText(Report["summary"]),
        FormatFindings(Report, Context),
        FormatEvidence(Report, Context),
    ]
    if Context.get("mention_comment") is not None:
        Sections.append(f"Mention comment: {Context['mention_comment']}")
    Sections.append(f"Review snapshot: {ObjectMap(Context['evidence'])['review_id']}")
    Content = "\n\n".join(Sections)
    if len(Content) > 60000:
        raise ValueError("Review exceeds GitHub publication limit")
    return Content
