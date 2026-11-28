from typing import cast as CastValue

from tests.Convert.Solidworks.Properties.RunPartText import (
    KPartCorpus,
    KPartProbe,
    RunPartText,
)

# the two contrasts isolate saved configuration identity and actual block manager ownership
KOwnerCauses = {
    "wrong_header_name": "part configuration properties differ from the saved ModelHeader name",
    "wrong_block_owner": "SOLIDWORKS sketch block map requires its owning backlink",
}


# the normal inspection and write routes must withhold text from contradictory native owners
def TestBoundText() -> None:
    ReportValue = RunPartText(
        KPartProbe / "CheckPartTextOwners.py",
        KPartCorpus / "part-properties/CircularProperties.SLDPRT",
    )
    assert ReportValue["native_header_names"] == ["modeled default", "shifted default"]
    assert ReportValue["native_block_link"] == [25227, 25229, 115, 2]
    assert ReportValue["typed_external_accesses"] == 0
    assert ReportValue["unscoped_text"] == [True, True, False]
    RowsValue = CastValue(dict[str, dict[str, object]], ReportValue["cases"])
    assert RowsValue.keys() == KOwnerCauses.keys()
    for NameValue, CauseValue in KOwnerCauses.items():
        StateValue = RowsValue[NameValue]
        InfoValue = CastValue(dict[str, str], StateValue["status"])
        assert InfoValue["status"] == "unsupported"
        assert InfoValue["diagnostic"] == CauseValue
        assert StateValue["text_scopes"] == [False, False, False]
        assert StateValue["configuration"] == ["modeled default", True, 0]
        assert StateValue["body"] == ["sldprt:body:1", 1, 1, 1]
        assert StateValue["geometry_equal"] is True
        TypedOwner = NameValue == "wrong_header_name"
        assert StateValue["typed_body_binding"] is TypedOwner
        assert StateValue["feature_count"] == (19 if TypedOwner else 27)
        assert StateValue["write_refusals"] == dict.fromkeys(
            ("strict_convert", "direct_write"),
            f"SOLIDWORKS part text properties are unavailable for writing ({CauseValue})",
        )
