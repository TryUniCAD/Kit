from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicGeom import (
    CheckPublicGeom,
)
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadWidthDepth import (
    ReadWidthDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoots import (
    CheckPrismRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# strict reconstruction needs the complete linked grammar and whole model inventory before any shape can be inferred
def CheckPrismScope(
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ModelValue: NativeModel,
    ColdValue: ColdOutput | None = None,
) -> Mapping[int, ArchiveNode]:
    RelationValue = ModelValue.WidthDepth
    CheckGeometry(LinkValue, ManagerValue, ModelValue, RelationValue=RelationValue)
    ProvenNodes: frozenset[ArchiveNode] = frozenset()
    if RelationValue is not None:
        if (
            ReadWidthDepth(ModelValue, LinkValue, RelationValue.SourceValue)
            != RelationValue
        ):
            raise ValueError("cache free prism equation ownership or state has changed")
        ProvenNodes = RelationValue.RelationNodes
    ColdAtom = None if ColdValue is None else ColdValue.AtomValue
    NodesValue = PrismNodes(LinkValue, ManagerValue, ColdAtom, ProvenNodes=ProvenNodes)
    Features = IndexFeatures(LinkValue)
    CheckPrismRoots(Features, NodesValue)
    CheckPrismRoot(LinkValue.ConfigValue.RootValue, ColdAtom)
    CheckPrismMgr(ManagerValue)
    if RelationValue is None:
        CheckPrismRels(LinkValue.ConfigValue.RootValue)
    CheckPublicGeom(ModelValue, Features)
    return Features
