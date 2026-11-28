import json as JsonTools
import sys as SysTools
from pathlib import Path
from typing import cast

from ObjectMap import ObjectMap


# model output is untrusted and must not directly select a github approval action
def ValidateReport(Value: object, Context: dict[str, object]) -> dict[str, object]:
    Report = ObjectMap(Value)
    if set(Report) != {
        "head",
        "base",
        "complete",
        "scope_matches",
        "score",
        "summary",
        "findings",
    }:
        raise ValueError("Unexpected report fields")
    Evidence = ObjectMap(Context["evidence"])
    if Report["head"] != Evidence["head_sha"] or Report["base"] != Evidence["base_sha"]:
        raise ValueError("Report revision mismatch")
    if type(Report["score"]) is not int or not 1 <= cast(int, Report["score"]) <= 5:
        raise ValueError("Score must be an integer between one and five")
    if (
        type(Report["complete"]) is not bool
        or type(Report["scope_matches"]) is not bool
    ):
        raise ValueError("Invalid report verdicts")
    if (
        not isinstance(Report["summary"], str)
        or not 1 <= len(Report["summary"]) <= 6000
    ):
        raise ValueError("Invalid review summary")
    Findings = Report["findings"]
    if not isinstance(Findings, list) or len(Findings) > 50:
        raise ValueError("Invalid findings inventory")
    Paths = {ObjectMap(Entry)["path"] for Entry in cast(list[object], Context["files"])}
    for Entry in cast(list[object], Findings):
        Finding = ObjectMap(Entry)
        if set(Finding) != {"priority", "path", "line", "title", "body"}:
            raise ValueError("Unexpected finding fields")
        if (
            Finding["priority"] not in ("P1", "P2", "P3")
            or Finding["path"] not in Paths
        ):
            raise ValueError("Invalid finding location or priority")
        if type(Finding["line"]) is not int or cast(int, Finding["line"]) < 1:
            raise ValueError("Invalid finding line")
        for Field in ("title", "body"):
            if (
                not isinstance(Finding[Field], str)
                or not 1 <= len(cast(str, Finding[Field])) <= 3000
            ):
                raise ValueError("Invalid finding text")
    return Report


if __name__ == "__main__":
    ValidateReport(
        JsonTools.loads(Path(SysTools.argv[1]).read_text()),
        ObjectMap(JsonTools.loads(Path(SysTools.argv[2]).read_text())),
    )
