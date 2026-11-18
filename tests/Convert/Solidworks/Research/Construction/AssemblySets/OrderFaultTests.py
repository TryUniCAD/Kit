from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import (
    MakeOrderCase,
)
from tests.Convert.Solidworks.Research.Construction.AssemblySets.RunOrderPhase import (
    RunOrderPhase,
)


# malformed prior mate state must reject before allocating another dimension feature wrapper or header event and preserve every observed publication counter
def TestOrderFaults() -> None:
    FaultValues = (
        "missing_prior",
        "duplicate_prior",
        "stale_header",
        "stale_config",
        "counter_reuse",
        "missing_log",
        "prior_owner",
        "wrapper_mate_id",
        "wrapper_absolute_id",
        "wrapper_endpoint_id",
        "prior_solved",
        "prior_alignment",
        "wrong_anchor",
        "prior_name",
        "foreign_component",
        "missing_dimension",
        "late_dimension",
        "dimension_collision",
        "replaced_prior_node",
        "replaced_dimension_node",
    )
    for FaultValue in FaultValues:
        Request: dict[str, object] = {
            "request": MakeOrderCase(("distance", "coincident", "parallel"), False),
            "fault": FaultValue,
        }
        Report = RunOrderPhase(Request, "fault")
        assert Report["rejected"] is Report["actual_parent_state_unchanged"] is True
        assert Report["before"] == Report["after"]
        assert Report["writer_output_count"] == 0
