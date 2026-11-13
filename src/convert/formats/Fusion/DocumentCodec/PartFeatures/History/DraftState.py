from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftEdges import (
    DraftEdges,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftFaces import (
    DraftFaces,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftFrame import (
    DraftFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
    KDraftState,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.LedgerTags import (
    LedgerTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.PlanBody import PlanBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody

KKernelVersion = "232.5.0.65535"


def DraftNodes(Plans: list[BodyPlan], FindIndex: DraftLookup) -> list[KDraftNode]:
    Nodes: list[KDraftNode] = [(("root",), AsmRoot(-1, -1, KKernelVersion))]
    for PlanValue in Plans:
        Nodes.extend(DraftFrame(PlanValue, FindIndex))
    for PlanValue in Plans:
        Nodes.extend(DraftFaces(PlanValue, FindIndex))
        Nodes.extend(DraftEdges(PlanValue, FindIndex))
    return Nodes


def DraftState(
    Bodies: tuple[ShapeBody, ...], Ledger: TagLedger, UnixMicros: float
) -> KDraftState:
    Plans = [
        PlanBody(BodyValue, Ordinal, FaceTags, BodyTag, UnixMicros)
        for Ordinal, (BodyValue, (FaceTags, BodyTag)) in enumerate(
            zip(Bodies, LedgerTags(Bodies, Ledger), strict=True)
        )
    ]
    KeyList = [NodeValue[0] for NodeValue in DraftNodes(Plans, DraftLookup(None))]
    Indices = {KeyValue: Index for Index, KeyValue in enumerate(KeyList)}
    if len(Indices) != len(KeyList):
        raise ValueError("Fusion part journal draft repeats a node identity")
    return tuple(DraftNodes(Plans, DraftLookup(Indices)))
