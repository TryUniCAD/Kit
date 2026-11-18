from tests.Convert.Solidworks.Research.Drawing.Named.MakeNamedJob import MakeNamedJob
from tests.Convert.Solidworks.Research.Drawing.Named.NamedCases import KNamedCases
from tests.Convert.Solidworks.Research.Drawing.Named.RunNamedCase import RunNamedCase


# every disclosed named family must preserve full stream identity and independent corner geometry across fresh designs
def TestNamedDefs() -> None:
    HashesValue: set[object] = set()
    for Arguments in KNamedCases:
        JobValue = MakeNamedJob(*Arguments)
        Result = RunNamedCase(JobValue)
        assert Result == RunNamedCase(JobValue)
        assert Result["passed"] and Result["all_logical_streams_identical"]
        assert Result["complete_sdk_readback"] and Result["sdk_read_write_identical"]
        assert Result["complete_research_readback"] and Result["public_reader_passed"]
        assert (
            Result["independent_canonical_frame"]
            and Result["independent_corner_projection"]
        )
        assert Result["independent_corner_count"] == 8
        assert Result["orientation"] == Arguments[1]
        assert Result["view_scale"] == Arguments[2]
        assert Result["front_profile_unchanged"]
        assert (
            Result["runtime_input_file_access_attempts"]
            == Result["heldout_inputs_read"]
            == 0
        )
        assert Result["research_semantic_factory_retained"]
        assert not Result["native_acceptance"]
        assert (
            not Result["vendor_runtime_executed"]
            and not Result["public_writer_enabled"]
        )
        assert Result["definition_map_next_index"] == 172
        HashesValue.add(Result["artifact_sha256"])
    assert len(HashesValue) == len(KNamedCases)
