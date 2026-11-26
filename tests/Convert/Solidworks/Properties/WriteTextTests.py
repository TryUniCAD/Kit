from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import (
    KPartCorpus,
    KPartProbe,
    RunPartText,
)

# the unsupported advanced manager with xml keeps its specific reader failure
KPartCause = "part properties require an empty compatible native manager"


# every ordinary write route refuses the inspected source before output publication
def TestTextRefusal() -> None:
    ReportValue = RunPartText(
        KPartProbe / "CheckWritePartText.py", KPartCorpus / "ladder/L1_boss.SLDPRT"
    )
    assert (
        ReportValue["source_sha256"]
        == "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
    )
    InfoValue = CastValue(dict[str, object], ReportValue["status"])
    assert (
        InfoValue["status"] == "unsupported" and InfoValue["diagnostic"] == KPartCause
    )
    assert ReportValue["diagnostics"] == [
        [
            "solidworks.part_text_properties_unavailable",
            "info",
            KPartCause,
        ]
    ]
    assert ReportValue["text_scopes"] == [False, False, False]
    assert ReportValue["configuration"] == ["Default", True, 0]
    assert ReportValue["body"] == ["sldprt:body:1", 1, 1, 1]
    assert ReportValue["implicit_path_unchanged"] is True
    assert ReportValue["refusals"] == dict.fromkeys(
        ("strict", "nonstrict", "public_write", "registry", "compatibility"),
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})",
    )
    NativeRefusals = CastValue(dict[str, str], ReportValue["native_copy_refusals"])
    assert NativeRefusals == dict.fromkeys(
        ("ordinary", "compatibility"),
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})",
    )
    Snapshot = CastValue(dict[str, object], ReportValue["neutral_snapshot"])
    assert Snapshot["body"] == ["portable:body", 1, 1, 1]
    assert Snapshot["configuration"] == ["Inspection", True, 0]
    assert Snapshot["feature_count"] == 1
    assert Snapshot["status"] == {"status": "unsupported", "diagnostic": KPartCause}
    assert Snapshot["diagnostics"] == ReportValue["diagnostics"]
    assert ReportValue["neutral_copies_refused"] == dict.fromkeys(
        ("ordinary", "compatibility", "source_relabel"),
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})",
    )
    assert ReportValue["filtered_copies_refused"] == dict.fromkeys(
        ("geometry", "mesh", "configuration"),
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})",
    )
