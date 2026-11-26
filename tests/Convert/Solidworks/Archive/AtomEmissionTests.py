from typing import cast as CastValue

from tests.Convert.Solidworks.Archive.RunAtomEmission import RunAtomEmission

# the two native manager spans use independent inherited archive counters
KSavedAtomCases = (
    (
        "ladder",
        [3062, 3174],
        [57, 59],
        "68a12eace31a252758266598f230aa648a4884726800855a23a41ed61cb73d13",
    ),
    (
        "concave",
        [2115, 2227],
        [50, 52],
        "cd514c6afb75ebccb1337b2ceb16b0a8bf328e3bddd930b3dc027a7db313e62e",
    ),
)


# saved bodies must retain their exact encoded bytes through the shared writer
def TestSavedAtoms() -> None:
    for CaseName, Interval, CounterRange, Digest in KSavedAtomCases:
        ReportValue = RunAtomEmission(CaseName)
        assert ReportValue["interval"] == Interval
        assert ReportValue["saved_range"] == CounterRange
        assert ReportValue["saved_count"] == 1
        assert ReportValue["native_body_sha256"] == Digest
        assert ReportValue["native_emission_sha256"] == Digest


# authored row growth and condition branches must change the stream by their modeled extent
def TestNewAtoms() -> None:
    ReportValue = RunAtomEmission("ladder")
    RowsValue = CastValue(list[dict[str, object]], ReportValue["authored"])
    assert [RowValue["count"] for RowValue in RowsValue] == [0, 1, 2, 1, 1, 1]
    assert [RowValue["size"] for RowValue in RowsValue] == [12, 100, 194, 92, 100, 100]
    assert [RowValue["conditions"] for RowValue in RowsValue] == [
        0,
        0,
        0,
        0x80,
        0x400000,
        0x400080,
    ]
    assert RowsValue[1]["states"] == [[-51, 1, 1, ["A", "alt"]]]
    assert RowsValue[2]["states"] == [[-51, 0, 0, ["A", "alt"]], [-52, 1, 1, "λ22"]]
    assert RowsValue[3]["states"] == [[37, 0x80000003, 0x80000003, "αλ"]]
    FirstUse = CastValue(dict[str, object], ReportValue["first_use"])
    assert FirstUse["allocation"] == [57, 58, 59]
    assert FirstUse["range"] == [57, 60]
    assert FirstUse["duplicate_declaration"] == "duplicate_class_declaration"
    assert ReportValue["refusals"] == [
        "inconsistent_state",
        "wrong_wire_type",
        "overflow_wire",
        "unmapped_model",
        "wrong_class",
        "nonzero_body_kind",
        "concept_link",
        "borrowed_atom",
        "duplicate_atom_id",
        "wrong_context",
        "wrong_version",
    ]
