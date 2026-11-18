from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAtom import (
    ReadBodyAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyCache import (
    ReadBodyCache,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument


# only coherent native body and archive ownership can qualify a source name projection
def ReadNamedBody(
    Document: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> BodyNameGraph:
    if len(Document.configurations) != 1 or len(Document.bodies) != 1:
        raise ValueError(
            "native names require the witnessed single configuration and body"
        )
    LinkValue = ReadNativeLink(Archive, ConfigId)
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
        )
    ):
        raise ValueError(
            "native name owners require complete nonprovisional archive grammar"
        )
    StreamName = LinkValue.ConfigName + "-Partition"
    NodesValue = ReadBodyCache(Document, Archive, StreamName)
    TreeValue = ReadBodyTree(NodesValue)
    BodyValue = NodesValue[TreeValue.BodyIndex]
    CheckXmtAttrs(NodesValue, BodyValue)
    Attributes = ReadBodyAttrs(NodesValue, BodyValue)
    LabelValue, ExplicitLabel = ReadKernelName(NodesValue, Attributes)
    AtomValue, FeatureId = ReadBodyAtom(
        LinkValue, NodesValue, Attributes, LabelValue, ExplicitLabel
    )
    if (
        Document.bodies[0].final_feature_id != f"sldprt:feature:{FeatureId}"
        or sum(
            Feature.id == Document.bodies[0].final_feature_id
            for Feature in Document.feature_timeline
        )
        != 1
    ):
        raise ValueError(
            "public body final feature differs from its actual native owner"
        )
    return BodyNameGraph(
        LinkValue,
        NodesValue,
        TreeValue,
        AtomValue,
        FeatureId,
        LabelValue,
        ExplicitLabel is not None,
        StreamName,
        len(Archive.require(StreamName)),
    )
