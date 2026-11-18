from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import (
    MakeAsmCase,
)
from tests.Convert.Solidworks.Research.Construction.Assembly.RunAsmPhase import (
    RunAsmPhase,
)


# malformed complete assemblies must fail before artifact publication while preserving the independently generated child and refusing partial native success
def TestAsmFaults() -> None:
    FaultValues = (
        "one_occurrence",
        "three_occurrences",
        "duplicate_occurrence",
        "nonrigid_frame",
        "feature_name_collision",
        "same_parent_child_path",
        "wrong_parent_kind",
        "provenance_disagreement",
        "wrong_effective_standard",
        "wrong_style_language",
        "wrong_child_manager_header",
        "wrong_child_model_class",
        "wrong_child_config_alias",
        "wrong_file_handle",
        "singular_transform",
        "wrong_child_config_owner",
    )
    for FaultValue in FaultValues:
        Request = MakeAsmCase("coincident", "y", False)
        Request["fault"] = FaultValue
        Result = RunAsmPhase(Request, "build")
        assert Result["rejected"] is Result["child_bytes_unchanged"] is True
        assert Result["writer_output_count"] == 0
