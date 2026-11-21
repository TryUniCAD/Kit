from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceAxis import (
    SourceAxis,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.SourceOps import (
    SourceOps,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceEnd import (
    ReadSourceEnd,
)
from interchange.document.Models.DocumentModel import CadDocument


# sketch normal selections must bind their actual operations profiles and datum even when the legacy direction vector is absent
def ReadSourceAxes(
    DocumentValue: CadDocument, OwnersValue: SourceOps
) -> tuple[SourceAxis, ...]:
    Result: list[SourceAxis] = []
    for FeatureValue, SketchValue in (
        (OwnersValue.StockValue, OwnersValue.StockSketch),
        (OwnersValue.CutValue, OwnersValue.CutSketch),
    ):
        Choices = tuple(
            Value
            for Value in DocumentValue.selections
            if Value.query.get("topology_role") == "direction_axis"
            and Value.query.get("native_owner_id")
            == FeatureValue.attributes.get("native_object_id")
        )
        if len(Choices) != 1 or len(Choices[0].path) != 1:
            raise ValueError("source operation lacks its one actual sketch normal")
        Choice = Choices[0]
        Element = Choice.path[0]
        if (
            set(Choice.query)
            != {"topology_role", "native_owner_id", "native_target_id"}
            or (Element.entity_kind, Element.entity_id, Element.subelement)
            != ("native", SketchValue.name, "N_Axis")
            or Choice.query.get("native_target_id")
            != SketchValue.attributes.get("native_object_id")
            or Choice.point is not None
            or Choice.attributes
        ):
            raise ValueError("source direction axis belongs to a different sketch")
        Plane = next(
            Value
            for Value in OwnersValue.PlaneValues
            if Value.PlaneId == SketchValue.support_plane_id
        )
        Direction = ReadSourceEnd(FeatureValue).direction
        if (
            Direction is not None
            and (Direction.x, Direction.y, Direction.z)
            != PrincipalFrame(Plane.AxisValue).NormalValue
        ):
            raise ValueError("source direction vector disagrees with its actual datum")
        Result.append(
            SourceAxis(Choice.id, FeatureValue.id, SketchValue.id, Plane.PlaneId)
        )
    return tuple(Result)
