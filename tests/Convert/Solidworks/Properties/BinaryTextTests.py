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

# an independently encoded nonzero unknown policy is outside the measured empty profile
KUnknownCause = "part property manager policy is outside the empty profile"

# the controls bind the unchanged advanced manager and the current empty manager
KAdvancedHash = "9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036"

# the changed signed policy is the only edit in the original advanced manager
KPolicyHash = "68ddf954035f094bc198fef05d289ca8550eb929d30c2d057944b1dbd48b7e91"

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
        ("unknown-policy", KUnknownCause),
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
    UnknownValue = CastValue(dict[str, object], ReportValue["unknown-policy"])
    assert (
        UnknownValue["property_xml"]
        == Advanced["property_xml"]
        == EmptyValue["property_xml"]
        == []
    )
    assert UnknownValue["result_manager_sha256"] == KPolicyHash
    AssertEmptyText(Advanced, KAdvancedHash, "Default", 26)
    AssertEmptyText(EmptyValue, KEmptyHash, "modeled default", 18)


# both physically different empty controls reach the independent native feature gate
def AssertEmptyText(
    StateValue: dict[str, object], HashValue: str, NameValue: str, OwnerId: int
) -> None:
    assert (
        StateValue["manager_sha256"] == StateValue["result_manager_sha256"] == HashValue
    )
    assert StateValue["status"] is None and StateValue["diagnostics"] == []
    assert StateValue["text_scopes"] == [False, False, False]
    assert StateValue["configuration"] == [NameValue, True, 0]
    assert StateValue["body"] == ["sldprt:body:1", 1, 1, 1]
    assert StateValue["geometry_equal"] is True
    Portability = CastValue(str, StateValue["portability_refusal"])
    assert Portability.startswith("native-only feature definitions cannot be exported")
    assert f"sldprt:feature:{OwnerId} (solidworks.sldprt:ProfileFeature)" in Portability
