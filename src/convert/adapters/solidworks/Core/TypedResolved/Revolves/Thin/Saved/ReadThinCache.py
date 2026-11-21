from convert.Geometry.Parasolid import DecodeBrepModel
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckNamedAtom import (
    CheckNamedAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import (
    ReadBodyKernel,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevolveTree import (
    ReadRevolveTree,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinState import (
    CheckThinState,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinMarks import (
    CheckThinMarks,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument


# even a semantics only read must join the feature and actual physical body through their original identities
def ReadThinCache(
    Document: CadDocument,
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    FeatureValue: ArchiveNode,
) -> tuple[BodyNameGraph, BrepModel]:
    StreamName = LinkValue.ConfigName + "-Partition"
    StreamValue = Archive.require(StreamName)
    Payloads, NodesValue, MarksValue = ReadBodyKernel(StreamValue, StreamName)
    TreeValue = ReadRevolveTree(NodesValue, False)
    BodyValue = NodesValue[TreeValue.BodyIndex]
    CheckXmtAttrs(NodesValue, BodyValue)
    Attributes = ReadBodyAttrs(NodesValue, BodyValue)
    NameValue, AuthoredName = ReadKernelName(NodesValue, Attributes)
    if AuthoredName is not None or NameValue != ReadNativeName(FeatureValue):
        raise ValueError("SOLIDWORKS saved thin body has an unresolved name")
    AtomValue, FeatureId = CheckNamedAtom(
        LinkValue, FeatureValue, NodesValue, Attributes, NameValue, AuthoredName
    )
    if not any(
        EntryValue.EntryValue is AtomValue
        for EntryValue in LinkValue.ConfigValue.MapValue.EntriesValue
    ):
        raise ValueError(
            "SOLIDWORKS thin body atom is outside the linked configuration"
        )
    CheckThinState(FeatureValue, LinkValue.ConfigValue.RootValue, AtomValue)
    CheckThinMarks(LinkValue.ConfigValue.RootValue, FeatureValue, MarksValue)
    ModelValue = DecodeBrepModel(Payloads[0].data)
    if ModelValue is None:
        raise ValueError("SOLIDWORKS thin partition has no usable boundary")
    if Document.brep is not None or Document.brep_payloads:
        Attached = tuple(
            (Value.kind, Value.source_stream, Value.sha256, Value.data)
            for Value in Document.brep_payloads
        )
        Expected = tuple(
            (Value.kind, StreamName, Value.sha256, Value.data) for Value in Payloads
        )
        if Document.brep != ModelValue or Attached != Expected:
            raise ValueError(
                "SOLIDWORKS thin body differs from the selected native cache"
            )
    return (
        BodyNameGraph(
            LinkValue,
            NodesValue,
            TreeValue,
            AtomValue,
            FeatureId,
            NameValue,
            False,
            StreamName,
            len(StreamValue),
        ),
        ModelValue,
    )
