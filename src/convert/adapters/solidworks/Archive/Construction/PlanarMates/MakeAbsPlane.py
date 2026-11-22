from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeAtomFeat import (
    MakeAtomFeat,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# detached mate references own an anonymous absolute plane built from the resolved world root and normal
def MakeAbsPlane(
    Assembly: ArchiveNode, FrameValue: PlaneFrame, Target: FeatureTarget
) -> ArchiveNode:
    Geometry: dict[str, object] = {
        "root": dict(zip(("x", "y", "z"), FrameValue.OriginValue, strict=True)),
        "normal": dict(zip(("x", "y", "z"), FrameValue.NormalValue, strict=True)),
        "f20": IdentityXform(),
        "f48": None,
        "f50": 0,
        "f54": 1,
        "f58": 2,
        "old_e5": 0,
        "f5c": 1,
        "f60": 0,
        "f64": 0,
        "f68": None,
        "f70": None,
        "f78": None,
    }
    Geometry.update({f"b{Index}": 0.0 for Index in range(4)})
    PlaneValue = MakeAtomFeat(Assembly, Target)
    PlaneValue.FieldsValue.update(
        {
            "f6c0": dict.fromkeys(("x", "y", "z"), 0.0),
            "f6dc": 4,
            "f6e0": 0,
            "f6e8": None,
            "f6f0": 0,
            "f6f8": ArchiveNode(RuntimeClass("moAbsoluteRefPlnData_c", 1), Geometry),
        }
    )
    return PlaneValue
