from ObjectMap import ObjectMap
from Publication.SafeText import SafeText


# collapsible evidence keeps revision and approval limitations available without obscuring the review verdict
def FormatEvidence(Report: dict[str, object], Context: dict[str, object]) -> str:
    Runtime = ObjectMap(Context["review_runtime"])
    GateInfo = ObjectMap(Context["approval_gate"])
    EvidenceRows = [
        (
            "Coverage",
            (
                "Complete"
                if Report["complete"] and Context["input_complete"]
                else "Incomplete; approval blocked"
            ),
        ),
        (
            "Scope",
            (
                "Matches claimed delivery"
                if Report["scope_matches"]
                else "Needs attention"
            ),
        ),
        ("Approval gate", GateInfo["reason"]),
        ("Reviewed head", Report["head"]),
        ("Reviewed base", Report["base"]),
        ("Model", f"{Runtime['model']} / {Runtime['reasoning_effort']} reasoning"),
        ("Trusted policy", Context["policy_sha"]),
    ]
    if GateInfo.get("run_id") is not None:
        EvidenceRows.append(("Approval CI run", GateInfo["run_id"]))
    if Context.get("generated_verification") is not None:
        EvidenceRows.append(
            ("Generated sources", "Exact trusted reconstruction verified")
        )
    Content = [
        "<details>",
        "<summary>Verification and approval checks</summary>",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    Content.extend(
        f"| {Label} | {SafeText(Value).replace('|', '&#124;')} |"
        for Label, Value in EvidenceRows
    )
    return "\n".join([*Content, "", "</details>"])
