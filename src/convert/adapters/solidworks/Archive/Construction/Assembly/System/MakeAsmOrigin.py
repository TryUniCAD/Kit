from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import (
    MakeOriginFix,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginSeed import (
    MakeOriginSeed,
)
from convert.adapters.solidworks.Archive.Construction.Origin.WireOriginMut import (
    WireOriginMut,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# assembly origin construction shares the classified profile and logical point rule while referencing its actual registered front plane
def MakeAsmOrigin(
    NameValue: str,
    OwnerValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    Component = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f990"])
    FieldsValue = CompRefFields(Component)
    FieldsValue.update(
        {
            "ff0": {"f00": PlaneValue.FieldsValue["f08"], "f08": 2592000},
            "ff8": None,
            "f100": 3,
        }
    )
    Reference = ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), FieldsValue)
    NodeValue = MakeAsmNode(
        "moOriginProfileFeature_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    SketchValue = MakeSketchSeed(NodeValue)
    NodeValue.FieldsValue.update(
        MakeOriginSeed(SketchValue, Reference, PrincipalFrame("z"))
    )
    PointValue = MakeRingPoint(SketchValue, (0.0, 0.0), 0)
    WireOriginMut(SketchValue, PointValue, MakeOriginFix(SketchValue, PointValue))
    return NodeValue
