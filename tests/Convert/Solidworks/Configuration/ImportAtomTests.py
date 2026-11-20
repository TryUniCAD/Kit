from tests.Convert.Solidworks.Configuration.ReadAtomCase import ReadAtomCase


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
