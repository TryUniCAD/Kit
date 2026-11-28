import re as RegexTools
from typing import cast

from ObjectMap import ObjectMap


# review text must not create notifications or executable markdown constructs
def SafeText(Value: object) -> str:
    return RegexTools.sub(r"[<>`\[\]\\]", "", str(Value)).replace("@", "＠")


# every reported issue remains visible even when it cannot be attached to a changed diff line
def ReviewBody(Report: dict[str, object]) -> str:
    Sections = [
        f"Soundness: {Report['score']}/5",
        f"Complete review: {Report['complete']}; scope matches: {Report['scope_matches']}",
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
    Content = "\n\n".join(Sections)
    if len(Content) > 60000:
        raise ValueError("Review exceeds GitHub publication limit")
    return Content
