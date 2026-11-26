from tests.Convert.Solidworks.Archive.RunHistoryCase import RunHistoryCase


# variable length comments must move emitted node spans without altering their source locations
def TestHistoryEdit() -> None:
    ReportValue = RunHistoryCase("edited")
    assert ReportValue["source_spans"] == [[0, 111], [56, 89]]
    assert ReportValue["emitted_spans"] == [[0, 135], [80, 113]]
    assert ReportValue["date_slot"] == 4
