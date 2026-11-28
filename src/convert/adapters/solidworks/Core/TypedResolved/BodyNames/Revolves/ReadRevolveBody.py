from math import isclose as IsClose, pi as CirclePi

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
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAuthor import (
    ReadBodyAuthor,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyCache import (
    ReadBodyCache,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevolveTree import (
    ReadRevolveTree,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)
from interchange.document.Models.DocumentModel import CadDocument


# only the complete measured ordinary revolve can extend native naming beyond the existing prism profile
def ReadRevolveBody(
    Document: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> BodyNameGraph:
    if len(Document.configurations) != 1 or len(Document.bodies) != 1:
        raise ValueError("revolve names require one configuration and actual body")
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
        raise ValueError("revolve names require complete nonprovisional owners")
    (OwnerValue,) = ReadRevOwners(LinkValue)
    IsFull = OwnerValue.EndValue.ModeValue == "one_sided" and IsClose(
        OwnerValue.AngleValue.RadiansValue, 2 * CirclePi, rel_tol=0, abs_tol=1e-12
    )
    StreamName = LinkValue.ConfigName + "-Partition"
    NodesValue, _ = ReadBodyCache(Document, Archive, StreamName)
    TreeValue = ReadRevolveTree(NodesValue, IsFull)
    BodyValue = NodesValue[TreeValue.BodyIndex]
    CheckXmtAttrs(NodesValue, BodyValue)
    Attributes = ReadBodyAttrs(NodesValue, BodyValue)
    if ReadBodyAuthor(LinkValue) is not None:
        raise ValueError(
            "ordinary revolve names require the witnessed derived atom state"
        )
    LabelValue, ExplicitLabel = ReadKernelName(NodesValue, Attributes)
    if ExplicitLabel is not None:
        raise ValueError("explicit revolve body names remain outside this profile")
    AtomValue, FeatureId = ReadBodyAtom(
        LinkValue,
        NodesValue,
        Attributes,
        LabelValue,
        ExplicitLabel,
        RevolveValue=OwnerValue.NodeValue,
    )
    if (
        Document.bodies[0].final_feature_id != f"sldprt:feature:{FeatureId}"
        or sum(
            Feature.id == Document.bodies[0].final_feature_id
            for Feature in Document.feature_timeline
        )
        != 1
    ):
        raise ValueError("public revolve body differs from the actual producing owner")
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
