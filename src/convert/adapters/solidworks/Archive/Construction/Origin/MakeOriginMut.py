from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import (
    MakeOriginFix,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginSeed import (
    MakeOriginSeed,
)
from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Origin.WireOriginMut import (
    WireOriginMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeSystemNode import (
    MakeSystemNode,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native origin construction needs its actual profile point relation and exclusive support wrapper while retaining pending first solve state
def MakeOriginMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    AxisValue: str,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> OriginGraph:
    Reference = MakeOriginRef(PlaneValue, OwnerValue, AxisValue)
    FrameValue = PrincipalFrame(AxisValue)
    ProfileValue = MakeSystemNode(
        "moOriginProfileFeature_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    SketchValue = MakeSketchSeed(ProfileValue)
    ProfileValue.FieldsValue.update(MakeOriginSeed(SketchValue, Reference, FrameValue))
    PointValue = MakeRingPoint(SketchValue, (0.0, 0.0), 0)
    Constraint = MakeOriginFix(SketchValue, PointValue)
    WireOriginMut(SketchValue, PointValue, Constraint)
    return OriginGraph(ProfileValue, SketchValue, PointValue, Constraint, Reference)
