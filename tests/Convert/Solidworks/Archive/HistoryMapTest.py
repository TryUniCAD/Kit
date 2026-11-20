from tests.Convert.Solidworks.Archive.RunHistoryCase import RunHistoryCase


# deleting a state moves the surviving date object to the first emitted map slot for that class
def TestHistoryMap() -> None:
    ReportValue = RunHistoryCase("renumbered")
    assert ReportValue["source_slots"] == [4, 5]
    assert ReportValue["post_write_source_slots"] == [4, 5]
    assert ReportValue["emitted_slot"] == 4
    assert ReportValue["map_counters"] == [6, 5]
    assert ReportValue["retained_build"] == 2040693
