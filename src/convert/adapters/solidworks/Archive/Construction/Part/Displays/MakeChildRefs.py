from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.VisualStates.DetachVisualRef import (
    DetachVisualRef,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# part visual references select the actual sketch origin and reverse ordered principal planes with matching creation logs
def MakeChildRefs(
    SystemValue: PartSystem,
    ProfileValue: ArchiveNode,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    UnitValue: ArchiveNode,
) -> tuple[ArchiveNode, ...]:
    Features = (
        RequireNode(ProfileValue, "moProfileFeature_c"),
        RequireNode(SystemValue.OriginValue.ProfileValue, "moOriginProfileFeature_c"),
        *(
            RequireNode(SystemValue.SystemValues.PlaneValues[AxisValue], "moRefPlane_c")
            for AxisValue in ("x", "y", "z")
        ),
    )
    FeatureIds = tuple(FieldInt(Feature.FieldsValue, "f08") for Feature in Features)
    if len(set(FeatureIds)) != len(Features) or min(FeatureIds) <= 0:
        raise ValueError(
            "part visual references require distinct actual feature identities"
        )
    Result: list[ArchiveNode] = []
    for Feature, FeatureId in zip(Features, FeatureIds, strict=True):
        FirstTime, SecondTime = (
            DatumTime(Header, FeatureId) for Header in HeadersValue
        )
        if (
            Feature.FieldsValue["owner"] is not SystemValue.RootValue
            or FieldInt(Feature.FieldsValue, "f2b0") != 19000
            or FirstTime != SecondTime
        ):
            raise ValueError(
                "part visual reference lost its actual feature or creation owner"
            )
        Fields = DetachVisualRef(UnitValue)
        Fields["ff0"] = {"f00": FeatureId, "f08": FirstTime}
        Result.append(ArchiveNode(RuntimeClass("moCompFeature_c", 1), Fields))
    return tuple(Result)
