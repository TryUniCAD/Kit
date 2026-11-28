import re as RegexTools
from typing import cast

from ObjectMap import ObjectMap


# review text must not create notifications or executable markdown constructs
def SafeText(Value: object) -> str:
    return RegexTools.sub(r"[<>`\[\]\\]", "", str(Value)).replace("@", "＠")


# every reported issue remains visible even when it cannot be attached to a changed diff line
def ReviewBody(Report: dict[str, object], Context: dict[str, object]) -> str:
    Sections = [
        f"Soundness: {Report['score']}/5",
        f"Complete review: {bool(Report['complete'] and Context['input_complete'])}; scope matches: {Report['scope_matches']}",
        SafeText(Report["summary"]),
    ]
    for Entry in cast(list[object], Report["findings"]):
        Finding = ObjectMap(Entry)
        Sections.append(
            f"{Finding['priority']} — {SafeText(Finding['title'])}\n\n"
            f"{SafeText(Finding['path'])}:{Finding['line']}\n\n{SafeText(Finding['body'])}"
        )
    Sections.append(
        f"Reviewed head: {Report['head']}\n\nReviewed base: {Report['base']}"
    )
    Runtime = ObjectMap(Context["review_runtime"])
    Sections.append(
        f"Model: {SafeText(Runtime['model'])}; reasoning: {SafeText(Runtime['reasoning_effort'])}"
    )
    Sections.append(
        f"Approval gate: {SafeText(ObjectMap(Context['approval_gate'])['reason'])}"
    )
    Sections.append(f"Policy revision: {Context['policy_sha']}")
    GateInfo = ObjectMap(Context["approval_gate"])
    if GateInfo.get("run_id") is not None:
        Sections.append(f"Approval CI run: {GateInfo['run_id']}")
    if not Context["input_complete"]:
        Sections.append(
            "Partial source coverage; automatic approval is disabled for this report"
        )
    if Context.get("mention_comment") is not None:
        Sections.append(f"Mention comment: {Context['mention_comment']}")
    Sections.append(f"Review snapshot: {ObjectMap(Context['evidence'])['review_id']}")
    Content = "\n\n".join(Sections)
    if len(Content) > 60000:
        raise ValueError("Review exceeds GitHub publication limit")
    return Content
