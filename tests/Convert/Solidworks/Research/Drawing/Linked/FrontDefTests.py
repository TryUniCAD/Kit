from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Linked.MakeFrontJob import MakeFrontJob
from tests.Convert.Solidworks.Research.Drawing.Linked.RunFrontCase import RunFrontCase


# complete linked definitions must preserve stream bytes and actual child identity across independent novel designs
def TestFrontDefs() -> None:
    HashesValue: set[object] = set()
    CasesValue = (
        ("LinkedAlpha", 0.0317, 0.0263, 0.0149),
        ("LinkedBeta", 0.0431, 0.0187, 0.0093),
        ("LinkedGamma", 0.0239, 0.0341, 0.0173),
        ("LinkedDelta", 0.0373, 0.0211, 0.0127),
    )
    for Label, Width, Height, Depth in CasesValue:
        JobValue = MakeFrontJob(Label, Width, Height, Depth)
        Request = CastValue(dict[str, object], JobValue["request"])
        ViewValue = CastValue(dict[str, object], Request["view"])
        if Label == "LinkedBeta":
            ViewValue["name"] = Label + " front Ω " + "v" * 360
        if Label == "LinkedGamma":
            ViewValue["position"] = [0.08873, 0.12719]
        if Label == "LinkedDelta":
            ViewValue["position"] = [0.15937, 0.06743]
        Result = RunFrontCase(JobValue)
        assert Result == RunFrontCase(JobValue)
        assert Result["passed"]
        assert Result["all_logical_streams_identical"]
        assert Result["complete_sdk_readback"] and Result["sdk_read_write_identical"]
        assert Result["complete_research_readback"]
        assert Result["public_reader_passed"]
        assert Result["blank_profile_unchanged"]
        assert Result["runtime_input_file_access_attempts"] == 0
        assert Result["heldout_inputs_read"] == 0
        assert Result["research_semantic_factory_retained"]
        assert not Result["native_acceptance"]
        assert not Result["vendor_runtime_executed"]
        assert not Result["public_writer_enabled"]
        assert Result["definition_map_next_index"] == 172
        HashesValue.add(Result["artifact_sha256"])
    assert len(HashesValue) == len(CasesValue)
