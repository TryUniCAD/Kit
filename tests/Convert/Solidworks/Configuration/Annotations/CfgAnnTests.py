from tests.Convert.Solidworks.Configuration.Annotations.RunAnnCase import RunAnnCase


# native ladder detailing must preserve both real inline owners and each nested frame
def TestLadderAnn() -> None:
    ReportValue = RunAnnCase("ladder")
    assert ReportValue["member_lengths"] == [1956, 388]
    assert ReportValue["native_incoming_counter"] == 69
    assert ReportValue["map_inherited"] == [1, 2, 3]
    assert ReportValue["frame_spans"] == [[17954, 18006], [18006, 18058]]
    assert ReportValue["annotation_base_count"] == 10
    assert ReportValue["unchanged_archive_bodies"] == 14


# the imported part provides different helper text length and an independent archive map
def TestConcaveAnn() -> None:
    ReportValue = RunAnnCase("concave")
    assert ReportValue["member_lengths"] == [1956, 412]
    assert ReportValue["native_incoming_counter"] == 54
    assert ReportValue["map_inherited"] == [1, 2, 3]
    assert ReportValue["frame_spans"] == [[16535, 16587], [16587, 16639]]
    assert ReportValue["annotation_base_count"] == 10
    assert ReportValue["unchanged_archive_bodies"] == 14


# independently built wire contrasts constrain signed selectors and unsupported object branches
def TestAnnWire() -> None:
    ReportValue = RunAnnCase("wire")
    assert ReportValue["positive_archives"] == 4
    assert ReportValue["different_frame_rows"] == [1, 0]
    assert ReportValue["string_array_count"] == 2
    assert ReportValue["signed_layer_selector"] == -2
    assert ReportValue["refusals"] == [
        "truncated",
        "trailing",
        "older_archive",
        "foreign_inline",
        "foreign_part",
        "layer_reference",
        "part_reference",
        "header_reference",
        "new_class",
        "datum_owners",
        "indicator_owners",
        "negative_indicator_count",
        "negative_frame_count",
    ]
