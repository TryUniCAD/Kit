from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.MakeEqToken import (
    MakeEqToken,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a local dimension wrapper clones its selected live handle and resolves it through its own part component
def MakeEqDimension(
    RootValue: ArchiveNode,
    DimensionValue: DimensionGraph,
    TokenText: str,
    StartValue: int,
) -> ArchiveNode:
    LiveValue = DimensionValue.HandleValue
    if LiveValue.FieldsValue["f58"] is not None:
        raise ValueError("local equation requires an independent live dimension handle")
    CloneValue = ArchiveNode(
        LiveValue.ClassValue, {**LiveValue.FieldsValue, "f58": MakeSelfComp(RootValue)}
    )
    WrapperValue = ArchiveNode(
        RuntimeClass("moDimRefWrapper_c", 1),
        {
            "fb0": DimensionValue.ParameterValue.FieldsValue["f58"],
            "f58": CloneValue,
            "f68": 0,
            "f60": None,
            "f6c": 0,
            "f08": 101,
            "has_f10": 0,
            "has_f18": 0,
            "f0c": -1,
            "f20": 0,
            "f74": -12345,
            "f78": -12345,
            "f7c": -12345,
            "f50": 0,
            "f70": LiveValue.FieldsValue["f4c"],
            "f34": 0,
            "f30": 0,
            "f98": 0,
            "f38": -1,
        },
    )
    return MakeEqToken(
        "moRelDimension_c",
        TokenText,
        StartValue,
        0,
        f30=MakeObList(),
        f78=None,
        f80=WrapperValue,
    )
