from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourcePlane import (
    SourcePlane,
)
from interchange.document.Models.DocumentModel import CadDocument


# every source datum must retain its real feature identity and canonical frame rather than borrowing a single active plane
def ReadSourcePlane(DocumentValue: CadDocument) -> tuple[SourcePlane, ...]:
    Result: list[SourcePlane] = []
    for PlaneValue in DocumentValue.support_planes:
        if (
            PlaneValue.support_selection_id is not None
            or PlaneValue.offset_parameter_id is not None
            or PlaneValue.attributes.get("principal") is not True
        ):
            raise ValueError("source datum has unrepresented reference semantics")
        NativeId = PlaneValue.attributes.get("native_object_id")
        Features = tuple(
            Value
            for Value in DocumentValue.feature_timeline
            if Value.attributes.get("native_object_id") == NativeId
        )
        if len(Features) != 1 or Features[0].name != PlaneValue.name:
            raise ValueError("source datum lacks its actual presentation feature")
        Result.append(
            SourcePlane(
                PlaneValue.id,
                Features[0].id,
                PlaneValue.name,
                ReadPrincAxis(PlaneValue.transform),
            )
        )
    if len(Result) != 3 or {Value.AxisValue for Value in Result} != {"x", "y", "z"}:
        raise ValueError("source owners require all three real principal datums")
    return tuple(Result)
