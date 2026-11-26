from typing import cast as CastValue


# additive direction evidence must retain every source diagnostic classification
def AxisIssues(Source: dict[str, object]) -> tuple[tuple[str, str], ...]:
    Issues = CastValue(list[dict[str, str]], Source["unresolved"])
    assert len(Issues) == 188
    assert sum(Issue["reason"] == "native_only_record" for Issue in Issues) == 25
    Classifications = tuple((Issue["path"], Issue["reason"]) for Issue in Issues)
    assert {
        Value for Value in Classifications if Value[0].startswith("/selections/0/")
    } == {
        ("/selections/0/path/0/entity_kind", "uninterpreted_native_value"),
        ("/selections/0/query", "unclassified_reference_semantics"),
        ("/selections/0/path/0/entity_id", "unresolved_reference"),
    }
    return Classifications
