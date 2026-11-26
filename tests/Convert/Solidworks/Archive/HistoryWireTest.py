from typing import cast as CastValue

from tests.Convert.Solidworks.Archive.RunHistoryCase import RunHistoryCase


# the wire control exercises caller supplied stamps counts native aliases and invalid owners
def TestHistoryWire() -> None:
    ReportValue = RunHistoryCase("authored")
    Biography = CastValue(dict[str, object], ReportValue["fresh_biography"])
    Histories = CastValue(list[dict[str, object]], ReportValue["fresh_histories"])
    assert (Biography["bytes"], Biography["n"], Biography["counter"]) == (23, 0, 3)
    assert [ItemValue["sha256"] for ItemValue in Histories] == [
        "2d6be58b68af7abc384bc55087606eab3bc1cf18b0b7cc8b3afb3c7b7a6438a1",
        "92ee8e39dc51a5bf4d1fedddcec1847c85b0c04ba5a4bef34a903c709a6722a7",
    ]
    assert [ItemValue["date_code"] for ItemValue in Histories] == [2031447, 2040693]
    assert [ItemValue["language"] for ItemValue in Histories] == [1033, 1041]
    assert ReportValue["aliased_date_history"] == {
        "authored_count_preserved": 9,
        "count": 2,
        "counter": 5,
        "date_slot": 4,
        "sha256": "544a6e6d5d83b2967a116d3c763a4496cab767cf532df1a1008c6c70d1b408f7",
    }
    assert ReportValue["refusals"] == [
        "negative_biography_count",
        "truncated_biography_row",
        "empty_version_history",
        "wrong_inner_version",
        "wrong_root_owner",
        "wrong_date_owner",
        "null_date_history",
        "wrong_date_alias",
        "empty_date_history",
        "trailing_bytes",
        "wrong_outer_version",
        "wrong_authored_date_owner",
    ]
