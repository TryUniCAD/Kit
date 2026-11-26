from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import (
    KPartCorpus,
    KPartProbe,
    RunPartText,
)

# each malformed input isolates a boundary the full configuration must enforce
KPhysicalCases = {
    "one_byte": (1, "no complete unsigned short"),
    "tail_truncated": (26054, "section exceeds its remaining stream"),
    "appended": (26056, "1 trailing bytes"),
    "wrong_owner": (26055, "component owner differs from its enclosing part"),
    "summary_only_truncated": (26054, "section exceeds its remaining stream"),
}


# unavailable property bags cannot cross either public publication boundary
def TestConfigText() -> None:
    ReportValue = RunPartText(
        KPartProbe / "CheckPhysicalPartText.py",
        KPartCorpus / "part-properties/CircularProperties.SLDPRT",
    )
    assert ReportValue["native_unit_owner"] == [2441, 2443, 2, 3]
    assert ReportValue["typed_external_accesses"] == 0
    RowsValue = CastValue(dict[str, dict[str, object]], ReportValue["cases"])
    assert RowsValue.keys() == KPhysicalCases.keys()
    for NameValue, (SizeValue, ReasonValue) in KPhysicalCases.items():
        StateValue = RowsValue[NameValue]
        InfoValue = CastValue(dict[str, str], StateValue["status"])
        assert InfoValue["status"] == "unsupported"
        CauseValue = InfoValue["diagnostic"]
        assert ReasonValue in CauseValue
        assert StateValue["config_bytes"] == SizeValue
        assert StateValue["removed_property_xml"] == (
            ["docProps/Config-0-Properties.xml", "docProps/custom.xml"]
            if NameValue == "summary_only_truncated"
            else []
        )
        assert StateValue["text_scopes"] == [False, False, False]
        assert StateValue["configuration"] == ["modeled default", True, 0]
        assert StateValue["body"] == ["sldprt:body:1", 1, 1, 1]
        assert StateValue["geometry_equal"] is True
        assert StateValue["write_refusals"] == dict.fromkeys(
            ("strict_convert", "direct_write"),
            f"SOLIDWORKS part text properties are unavailable for writing ({CauseValue})",
        )
