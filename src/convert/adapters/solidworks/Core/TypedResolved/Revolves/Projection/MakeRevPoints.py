from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)


# point identities and adjacency survive replacement of the heuristic sketch entities
def MakeRevPoints(ProfileValue: RevolveProfile) -> tuple[Mapping[str, object], ...]:
    PointsValue = (
        *ProfileValue.LoopValue.PointsValue,
        *ProfileValue.AxisPoints.values(),
    )
    return tuple(
        {
            "array_index": PointValue.IndexValue,
            "native_creation_id": PointValue.CreationId,
            "native_fields": PointValue.FieldsValue,
            "line_handles": tuple(
                {
                    "class": HandleValue.ClassValue.NameValue,
                    "object_index": HandleValue.IndexValue,
                    "fields": dict(HandleValue.FieldsValue),
                }
                for HandleValue in PointValue.HandlesValue
            ),
        }
        for PointValue in PointsValue
    )
