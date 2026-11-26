from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunCacheCase import RunCacheCase

# the digest binds every inline property to the independent field decoder
KOneSlotFields = "70229093de36e8adb9f63153002a41fe64cf72c8856ec9eddf6d68ddc1d5c9ad"


# one populated mass slot must end before any signed selector word
def TestCacheSlot() -> None:
    ReportValue = RunCacheCase("one-slot")
    Records = CastValue(dict[str, dict[str, object]], ReportValue["records"])
    MassValue = Records["mass"]
    Fields = CastValue(dict[str, object], MassValue["fields"])
    (SlotValue,) = CastValue(list[dict[str, object]], Fields["f1628"])
    assert SlotValue["n10"] == 1
    assert SlotValue["f08"] == [{"atom": 211, "v": -40, "d": 0.625}]
    assert len(CastValue(dict[str, object], SlotValue["f18"])) == 33
    assert Fields["f1638"] == 0
    assert MassValue["bytes"] == 305
    assert MassValue["fields_sha256"] == KOneSlotFields
    assert MassValue["counter"] == 108
    assert MassValue["anchor_slots"] == [1, 2, 3]
    assert ReportValue["appended_selector"] == -23
    assert ReportValue["refusals"] == ["selector_after_one_slot"]
    assert ReportValue["reference_refusal"] == "cache reference has trailing data"
