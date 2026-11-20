from tests.Convert.Solidworks.Configuration.ReadAtomCase import ReadAtomCase


# the scoped reader must retain separate signed owners and the effective atom state
def AssertAtomWire(ReportValue: dict[str, object]) -> None:
    assert ReportValue["authored"] == {
        "counter": [59, 61],
        "slots": [59, 60],
        "values": [[2147483651, 0, -19, -31, -41], [1, 1, 207, -31, -41]],
        "manager_tail": 2882400001,
        "names": [["A", "alt"], ["A", "alt"]],
    }
    assert ReportValue["context"] == [
        [128, 76, [2147483651, 2147483651, -19, -31, -41], None],
        [4194432, 88, [2147483651, 2147483651, -19, -31, -41], -7],
    ]


# the extrusion output must resolve the actual atom while retaining its separate feature id
def TestLadderAtom() -> None:
    ReportValue = ReadAtomCase("ladder")
    assert ReportValue["interval"] == [3062, 3174]
    assert ReportValue["counter"] == [57, 59]
    assert ReportValue["original_entry_count"] == 56
    assert ReportValue["header_standalone_slot"] == 69
    assert ReportValue["atom_slot"] == 58
    assert ReportValue["atom"] == [0, 0, 101, 34, 34]
    assert ReportValue["body_stamps"] == [1656, 1656]
    assert ReportValue["producer"] == {
        "class": "moExtrusion_c",
        "feature_slot": 234,
        "feature_id": 34,
        "output_id": 101,
        "reference_slot": 58,
    }
    AssertAtomWire(ReportValue)
    AssertAtomBad(ReportValue["refusals"])


# malformed payloads and unqualified archive roles must fail before reporting a manager
def AssertAtomBad(Refusals: object) -> None:
    assert Refusals == [
        "truncated",
        "trailing",
        "wrong_version",
        "detached_part",
        "wrong_schema",
        "null_atom",
        "borrowed_atom",
        "duplicate_ids",
        "negative_count",
        "named_owner",
        "list_tail",
        "body_kind_-1",
        "body_kind_1",
        "body_kind_2",
    ]


# the imported feature has independent archive slots and still uses the same atom wire grammar
def TestConcaveAtom() -> None:
    ReportValue = ReadAtomCase("concave")
    assert ReportValue["interval"] == [2115, 2227]
    assert ReportValue["counter"] == [50, 52]
    assert ReportValue["original_entry_count"] == 49
    assert ReportValue["header_standalone_slot"] == 15
    assert ReportValue["atom_slot"] == 51
    assert ReportValue["atom"] == [0, 0, 101, 18, 18]
    assert ReportValue["body_stamps"] == [0, 0]
    assert ReportValue["producer"] == {
        "class": "moBaseBody_c",
        "feature_slot": 154,
        "feature_id": 18,
        "output_id": 101,
        "reference_slot": 51,
    }
