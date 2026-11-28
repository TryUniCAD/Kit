from pytest import mark as MarkTest
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.HeaderEpoch.MakeEpochProbe import (
    MakeEpochProbe,
)
from tests.Convert.Solidworks.Research.Mates.HeaderEpoch.RunEpochProbe import (
    RunEpochProbe,
)


# malformed real header lists and epochs must reject before parent ids reference counters or fixed anchor state change
@MarkTest.parametrize("ViewValue", ("body", "sdk"))
@MarkTest.parametrize(
    "FaultValue",
    (
        "duplicate_log",
        "invalid_epoch",
        "overflow_epoch",
        "boolean_epoch",
        "wrong_log_class",
        "wrong_stamp_class",
        "wrong_log_schema",
        "wrong_stamp_schema",
        "invalid_items",
        "wrong_count",
        "wrong_list_owner",
        "bad_row",
    ),
)
def TestEpochReject(ViewValue: str, FaultValue: str) -> None:
    ResultValue = RunEpochProbe(
        MakeEpochProbe("y", "authored", ViewValue, FaultValue=FaultValue)
    )
    assert ResultValue["passed"] is ResultValue["rejected"] is True
    assert ResultValue["writer_output_count"] == 0
    assert ResultValue["runtime_file_read_attempts"] == 0
    Rejection = CastValue(dict[str, object], ResultValue["rejection"])
    assert Rejection["parent_state_unchanged"] is True
    assert Rejection["before"] == Rejection["after"]
