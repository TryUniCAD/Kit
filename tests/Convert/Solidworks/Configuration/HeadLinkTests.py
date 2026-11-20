from tests.Convert.Solidworks.Configuration.RunHeadLink import RunHeadLink

# the controls have distinct native self slots and lightweight boundaries
KHeadLinkCases = (("ladder", 3052, 69, "Part1"), ("concave", 2105, 15, "ConcaveOwned"))

# a present standalone header cannot substitute for an invalid or missing named model header
KLinkRefusals = [
    "missing_model_header",
    "malformed_model_header",
    "header_tail",
    "missing_configuration",
    "one_byte_configuration",
    "null_root",
    "other_root",
    "other_root_schema",
    "truncated_light_header",
    "small_light_frame",
    "oversized_light_frame",
    "other_container_version",
]


# the fresh part map inherits the true header node by identity at the actual section start
def TestPartHead() -> None:
    for CaseName, EndValue, NativeIndex, FileName in KHeadLinkCases:
        ReportValue = RunHeadLink(CaseName)
        assert ReportValue["root"] == ["moPart_c", 1, 2]
        assert ReportValue["lightweight_span"] == [18, EndValue]
        assert ReportValue["map_slots"] == [1, 2, 3]
        assert ReportValue["header_index"] == NativeIndex
        assert ReportValue["config_index"] == 3
        assert ReportValue["base"] == ReportValue["counter"] == 4
        assert ReportValue["file_identity"] == [FileName, 2, "Default"]
        SameRoleBytes = (
            ReportValue["model_header_sha256"]
            == ReportValue["standalone_header_sha256"]
        )
        assert SameRoleBytes is (CaseName == "ladder")
        assert ReportValue["refusals"] == (
            KLinkRefusals if CaseName == "concave" else []
        )
