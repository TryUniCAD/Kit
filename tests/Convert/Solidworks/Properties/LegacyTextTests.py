from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import (
    KPartProbe,
    KProjectPath,
    RunPartText,
)

# the wheel smoke conversion starts with this structurally empty legacy property file
KLegacyPart = KProjectPath / "re/solidworks/examples/.SLDPRT/example.SLDPRT"


# legacy strict inspection preserves the solid and separates support and property refusals
def TestLegacyText() -> None:
    ReportValue = RunPartText(KPartProbe / "CheckLegacyPartText.py", KLegacyPart)
    assert (
        ReportValue["source_sha256"]
        == "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408"
    )
    assert ReportValue["archive_version"] == 18000
    Portability = CastValue(str, ReportValue["original_portability_refusal"])
    assert Portability.startswith("unqualified SOLIDWORKS sketch support references")
    assert Portability.endswith("sldprt:sketch:40")
    AuthoredPortability = CastValue(str, ReportValue["authored_portability_refusal"])
    assert AuthoredPortability.startswith(
        "unqualified SOLIDWORKS sketch support references"
    )
    assert AuthoredPortability.endswith("sldprt:sketch:40")
    Original = CastValue(dict[str, object], ReportValue["original"])
    Authored = CastValue(dict[str, object], ReportValue["authored_title"])
    assert Original["status"] is None
    assert Original["text_scopes"] == [False, False, False]
    assert Original["body"] == Authored["body"] == ["sldprt:body:1", 1, 1, 1]
    assert (
        Original["configuration"] == Authored["configuration"] == ["Default", True, 0]
    )
    assert Authored["diagnostics"] == [
        [
            "solidworks.part_text_properties_unavailable",
            "info",
            "legacy SOLIDWORKS part contains authored summary text",
        ]
    ]
    assert ReportValue["refusal"] == (
        "SOLIDWORKS part text properties are unavailable for writing "
        "(legacy SOLIDWORKS part contains authored summary text)"
    )
