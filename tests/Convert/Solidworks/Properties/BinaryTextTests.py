from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import (
    KPartCorpus,
    KPartProbe,
    KProjectPath,
    RunPartText,
)

# the nested refusal retains the owning schema and cursor path from the body executor
KOwnerCause = (
    "SOLIDWORKS body moCusPropMgr_c field f20 at 56: "
    "SOLIDWORKS body moCusPropMgr_c field f20/o at 56: "
    "part property manager has unsupported owner placement"
)

# the scoped modern lane requires the measured empty native manager
KAdvancedCause = "part properties require an empty compatible native manager"

# the controls bind the unchanged advanced manager and the current empty manager
KAdvancedHash = "9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036"

# the supported empty control must retain the original manager bytes
KEmptyHash = "becd5b67dff32e75102e20443e9e3a3f3def6896ebf05ae7dc188bcaae57ff58"


# binary owners are checked with every property scope absent and geometry stays readable
def TestBinaryText() -> None:
    ReportValue = RunPartText(
        KPartProbe / "CheckBinaryPartText.py",
        KProjectPath / "re/solidworks/examples/.SLDPRT/example.SLDPRT",
        KPartCorpus / "ladder/L1_boss.SLDPRT",
        KPartCorpus / "part-properties/CircularProperties.SLDPRT",
    )
    for NameValue, CauseValue in (
        ("malformed", KOwnerCause),
        ("advanced", KAdvancedCause),
    ):
        StateValue = CastValue(dict[str, object], ReportValue[NameValue])
        assert StateValue["geometry_equal"] is True
        assert StateValue["manager_sha256"] == KAdvancedHash
        assert StateValue["body"] == ["sldprt:body:1", 1, 1, 1]
        assert StateValue["configuration"] == ["Default", True, 0]
        assert StateValue["text_scopes"] == [False, False, False]
        assert StateValue["diagnostics"] == [
            [
                "solidworks.part_text_properties_unavailable",
                "info",
                CauseValue,
            ]
        ]
        assert StateValue["refusal"] == (
            f"SOLIDWORKS part text properties are unavailable for writing ({CauseValue})"
        )
    Advanced = CastValue(dict[str, object], ReportValue["advanced"])
    Malformed = CastValue(dict[str, object], ReportValue["malformed"])
    LegacySupport = CastValue(str, Malformed["portability_refusal"])
    assert LegacySupport.startswith("unqualified SOLIDWORKS sketch support references")
    assert LegacySupport.endswith("sldprt:sketch:40")
    EmptyValue = CastValue(dict[str, object], ReportValue["empty"])
    assert EmptyValue["manager_sha256"] == KEmptyHash
    assert Advanced["property_xml"] == EmptyValue["property_xml"] == []
    assert EmptyValue["status"] is None and EmptyValue["diagnostics"] == []
    assert EmptyValue["text_scopes"] == [False, False, False]
    assert EmptyValue["configuration"] == ["modeled default", True, 0]
    assert EmptyValue["body"] == ["sldprt:body:1", 1, 1, 1]
    assert EmptyValue["geometry_equal"] is True
    Portability = CastValue(str, EmptyValue["portability_refusal"])
    assert Portability.startswith("native-only feature definitions cannot be exported")
    assert "sldprt:feature:-1 (solidworks.sldprt:Sheet-Metal Master)" in Portability
