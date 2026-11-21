from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Circles.RequireRadial import (
    RequireRadial,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckViewArgs import (
    CheckViewArgs,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireSketch import (
    RequireSketch,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# common display reuse must verify the actual owner dimension kind release and authored presentation instead of widening a mate guard blindly
def RequireDisplay(
    HandleValue: ArchiveNode, DesignIntent: bool, SelectedLeader: int, TextKind: int
) -> ArchiveNode:
    if isinstance(
        CastValue(object, HandleValue), ArchiveNode
    ) and HandleValue.ClassValue == RuntimeClass("moSkDimHandleRadial_c", 1):
        OwnerValue = RequireRadial(HandleValue, TextKind)
        CheckViewArgs(DesignIntent, SelectedLeader)
        return OwnerValue
    if isinstance(
        CastValue(object, HandleValue), ArchiveNode
    ) and HandleValue.ClassValue == RuntimeClass("moSkDimHandleValG2_c", 1):
        OwnerValue = RequireSketch(HandleValue, TextKind)
        CheckViewArgs(DesignIntent, SelectedLeader)
        return OwnerValue
    _ = RequireNode(HandleValue, "moFeatureDimHandle_c")
    OwnerValue = ArchiveNode.RequireNode(HandleValue.FieldsValue.get("owner"))
    if (
        OwnerValue.ClassValue
        not in (
            RuntimeClass("moMateDistanceDim_c", 1),
            RuntimeClass("moExtrusion_c", 1),
            RuntimeClass("moICE_c", 1),
            RuntimeClass("moRevolution_c", 1),
            RuntimeClass("moRevCut_c", 1),
            RuntimeClass("moRevolutionThin_c", 1),
        )
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
    ):
        raise ValueError(
            "display reuse requires a verified current mate distance extrusion or angular revolve owner"
        )
    Dimension = ArchiveNode.RequireNode(HandleValue.FieldsValue.get("ff0"))
    IsAngular = Dimension.ClassValue == RuntimeClass("AngleDim_c", 1)
    if Dimension.ClassValue not in (
        RuntimeClass("ParallelPlaneDistanceDim_c", 1),
        RuntimeClass("AngleDim_c", 1),
    ):
        raise ValueError(
            "display reuse requires its actual local distance or angle dimension"
        )
    ExpectedKind = (
        18
        if OwnerValue.ClassValue.NameValue == "moMateDistanceDim_c"
        else 13 if IsAngular else 2
    )
    if (
        type(CastValue(object, TextKind)) is not int
        or TextKind != ExpectedKind
        or IsAngular
        and OwnerValue.ClassValue.NameValue
        not in ("moExtrusion_c", "moRevolution_c", "moRevCut_c", "moRevolutionThin_c")
        or OwnerValue.ClassValue.NameValue in ("moRevolution_c", "moRevCut_c")
        and not IsAngular
    ):
        raise ValueError(
            "display text kind disagrees with its verified native factory and dimension owner"
        )
    CheckViewArgs(DesignIntent, SelectedLeader)
    return OwnerValue
