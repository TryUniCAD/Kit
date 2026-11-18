from pathlib import PurePosixPath, PureWindowsPath
from typing import cast as CastValue


# host output identity must remain separate from the neutral self locator without renaming the actual model or weakening existing windows byte behavior
def AssertHostPath(ReportValue: dict[str, object]) -> int:
    for NameValue in (
        "exact_basename",
        "exact_direct_candidate",
        "windows_bytes_preserved",
        "staging_and_memory_bytes_equal",
        "memory_sink_unchanged",
        "no_filesystem_mapping_claim",
    ):
        assert ReportValue[NameValue] is True
    HostValue = PurePosixPath(CastValue(str, ReportValue["final_host_path"]))
    SelfValue = PureWindowsPath(CastValue(str, ReportValue["native_self_locator"]))
    assert HostValue.is_absolute() and HostValue.name == SelfValue.name
    assert HostValue.stem == SelfValue.stem == ReportValue["neutral_name"]
    assert str(SelfValue.parent) == r"C:\KitSdkCandidates"
    assert len(CastValue(dict[str, object], ReportValue["streams"])) == 10
    Failures = CastValue(list[dict[str, object]], ReportValue["malformed"])
    assert len(Failures) == 13 and all(RowValue["rejected"] for RowValue in Failures)
    return CastValue(int, ReportValue["bytes"])
