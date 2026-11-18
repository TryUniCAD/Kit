from pytest import mark as MarkTest
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput
from tests.Convert.Solidworks.Research.Mates.Distance.RunSdkDistance import (
    RunSdkDistance,
)


# invalid distance inputs and actual graph state must reject before either identity or parent fixed and wrapper state changes
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
        "zero_length",
        "negative_length",
        "short_length",
        "nonfinite_length",
        "boolean_length",
        "invalid_design_intent",
        "invalid_leader",
        "nonpositive_separation",
        "opposite_normals",
        "unsupported_tolerance",
        "centered_text",
        "insufficient_id_room",
    ),
)
def TestDistReject(FaultValue: str) -> None:
    ResultValue = RunSdkDistance(MakeDistInput("y"), FaultValue=FaultValue)
    assert ResultValue["passed"] is ResultValue["rejected"] is True
    assert ResultValue["writer_output_count"] == 0
    assert ResultValue["runtime_file_read_attempts"] == 0
    Rejection = CastValue(dict[str, object], ResultValue["rejection"])
    assert Rejection["parent_state_unchanged"] is True
    assert Rejection["before"] == Rejection["after"]
