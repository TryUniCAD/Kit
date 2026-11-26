from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunCacheCase import RunCacheCase

# the digest covers every inline cache field independently decoded from the authored wire
KAuthoredFields = "89727816989f7e4682c5cc735d9e9a17dbc796ec2a37ee2fa444fd7008acf178"


# the two slot frame reads the actual atom rows and the conditional signed trailer
def TestCacheWire() -> None:
    ReportValue = RunCacheCase("authored")
    Records = CastValue(dict[str, dict[str, object]], ReportValue["records"])
    MassValue = Records["mass"]
    FieldsValue = CastValue(dict[str, object], MassValue["fields"])
    SlotsValue = CastValue(list[dict[str, object]], FieldsValue["f1628"])
    assert len(SlotsValue) == 2
    assert [SlotValue["n10"] for SlotValue in SlotsValue] == [0, 2]
    assert "f18" not in SlotsValue[0]
    assert "f18" in SlotsValue[1]
    assert FieldsValue["f1638"] == -17
    assert MassValue["fields_sha256"] == KAuthoredFields
    assert MassValue["layouts"] == [
        "mgVector_c.restore",
        "moMassPropCache_c.Serialize",
        "moMassProp_c",
    ]
    assert MassValue["bytes"] == 329
    assert MassValue["counter"] == 108
    assert MassValue["anchor_slots"] == [1, 2, 3]
    assert ReportValue["refusals"] == [
        "negative_count",
        "oversized_count",
        "negative_atom_count",
        "truncated_selector",
        "mass_surplus",
        "bounds_owner",
        "bounds_surplus",
        "missing_part",
        "version",
    ]
