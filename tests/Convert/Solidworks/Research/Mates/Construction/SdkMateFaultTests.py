from pytest import mark as MarkTest
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.Construction.MakeSdkMate import MakeSdkMate
from tests.Convert.Solidworks.Research.Mates.Construction.RunSdkMate import RunSdkMate


# malformed actual graph state must fail before native output while parent allocation counters and anchors remain unchanged
@MarkTest.parametrize(
    "FaultValue",
    (
        "foreign_occurrence",
        "wrong_external_backlink",
        "wrong_child_configuration",
        "stale_child_update",
        "wrong_datum_owner",
        "unregistered_datum",
        "bad_datum_bounds",
        "scaled_placement",
        "reflected_placement",
        "repeated_selection",
        "foreign_fixed_input",
        "wrong_allocator_boundary",
        "wrapper_counter_exhausted",
        "unsupported_kind",
        "invalid_mate_name",
        "invalid_creation_epoch",
        "unsupported_parent_schema",
        "unsupported_child_schema",
        "unsupported_datum_version",
        "overflowing_inverse_frame",
    ),
)
def TestMateReject(FaultValue: str) -> None:
    Outcome = RunSdkMate(MakeSdkMate("coincident", "y"), FaultValue=FaultValue)
    assert Outcome["passed"] is Outcome["rejected"] is True
    assert Outcome["writer_output_count"] == 0
    assert Outcome["runtime_file_read_attempts"] == 0
    assert Outcome["native_processes_started"] == 0
    Rejection = CastValue(dict[str, object], Outcome["rejection"])
    assert Rejection["parent_state_unchanged"] is True
    assert Rejection["fault"] == FaultValue
    assert Rejection["before"] == Rejection["after"]
