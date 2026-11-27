from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimBody import CheckRimBody
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimCaches import (
    CheckRimCaches,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimMgrs import (
    CheckRimMgrs,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimModes import (
    CheckRimModes,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPassive import (
    CheckRimPassive,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimProgen import (
    CheckRimProgen,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimRef import CheckRimRef
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimSelect import (
    CheckRimSelect,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimParams import (
    ReadRimParams,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimClasses import KRimClasses
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Policy.CheckAssembly import CheckAssembly
from convert.adapters.Fusion.Native.Policy.CheckClasses import CheckClasses
from convert.adapters.Fusion.Native.Policy.CheckContainers import CheckContainers
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.CheckFeature import CheckFeature
from convert.adapters.Fusion.Native.Policy.CheckPlacement import CheckPlacement
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.DesignClasses import KDesignClasses
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# complete source policy must pass before the specialized geometry can justify neutral fillet admission
def CheckRimPolicy(
    Model: DocumentModel, Graph: NativeGraph, Context: RimContext
) -> None:
    Extrusion = Context.Extrusion
    CheckClasses(Graph, Additional=KRimClasses)
    CheckAssembly(Graph, Extrusion)
    CheckContainers(Graph, Extrusion)
    CheckPlacement(Graph, Extrusion)
    for Feature in (Extrusion.SketchFeature, Extrusion.Extrude, Context.Feature):
        CheckFeature(Graph, Feature)
    CheckExtrusion(Graph, Extrusion)
    CheckScopes(Graph, Extrusion, Model.Asset.AssetId)
    CheckRimModes(Context)
    _ = ReadRimParams(Graph, Context)
    CheckRimSelect(Graph, Context, Model.Asset.AssetId)
    CheckRimMgrs(Graph, Context)
    CheckRimCaches(Graph, Context, Model.Asset.AssetId)
    CheckRimBody(Graph, Context)
    CheckRimPassive(Graph, Context)
    CheckRimProgen(Graph, Context)
    for Value in Graph.Nodes.values():
        if Value.SegmentId != 0 and (
            Value.ClassName in KDesignClasses or Value.ClassName in KRimClasses
        ):
            raise ValueError("Native rim semantic owner uses another design segment")
        if any(Group.Opaque is not None for Group in Value.Groups):
            raise ValueError("Native rim source contains opaque semantic members")
        CheckRimRef(Value.Groups, Graph, Value.SegmentId)
