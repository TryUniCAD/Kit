from convert.Geometry.Parasolid import DecodeBrepModel, DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalLabel import (
    ReadLocalLabel,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalTree import (
    ReadLocalTree,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.LinkLocalBody import (
    LinkLocalBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyBrep import (
    ReadLocalBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import (
    ReadLocalNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    CheckSoleGroup,
    ReadLocalPay,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadTrimOnly import (
    ReadTrimMarks,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind


# design reads can bind physical local storage even when they omit the public geometry and its payloads
def ReadLocalSource(
    Document: CadDocument, Archive: SldprtArchive, LocalStream: bytes
) -> tuple[bytes, int]:
    if Document.brep is not None:
        return ReadLocalPay(Document.brep_payloads, Archive.require(KPartitionStream))
    CheckSoleGroup(Archive, "local body names")
    (FrameValue,) = DecodePartData(LocalStream, KLocalBodyStream)
    if FrameValue.kind != "unknown":
        raise ValueError("local body names require the selected local frame")
    MarkValue, _ = ReadTrimMarks(Archive, "local body names")
    return FrameValue.data, MarkValue


# the selected archive feature and public geometry must belong to the same local body
def ReadLocalName(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int | None,
    *,
    DesignOnly: bool = False,
) -> BodyNameGraph:
    Configurations = Document.configurations
    if (
        ConfigId != 0
        or len(Configurations) != 1
        or Configurations[0].id != "sldprt:configuration:0"
        or not Configurations[0].active
        or len(Document.bodies) != 1
        or (Document.brep is None and not DesignOnly)
    ):
        raise ValueError(
            "local body names require the selected complete single configuration"
        )
    LocalStream = Archive.require(KLocalBodyStream)
    LocalData, MarkValue = ReadLocalSource(Document, Archive, LocalStream)
    GroupKey = ReadLocalWrap(LocalStream, LocalData)
    LinkValue = ReadNativeLink(Archive, ConfigId)
    AtomValue, FeatureId = ReadLocalOwner(LinkValue, GroupKey, MarkValue)
    PublicId = f"sldprt:feature:{FeatureId}"
    StepsValue = tuple(
        Feature for Feature in Document.feature_timeline if Feature.id == PublicId
    )
    if (
        Document.bodies[0].final_feature_id != PublicId
        or len(StepsValue) != 1
        or StepsValue[0].kind != FeatureKind.IMPORTED
        or StepsValue[0].name != GroupKey
        or PublicId in Configurations[0].suppressed_feature_ids
    ):
        raise ValueError(
            "public design body does not belong to the selected native import"
        )
    NodesValue, _ = ReadLocalNodes(LocalData)
    TreeValue = ReadLocalTree(NodesValue)
    if Document.brep is not None:
        ModelValue = DecodeBrepModel(LocalData) or ReadLocalBrep(
            Document.brep_payloads, LocalStream, GroupKey, Archive=Archive
        )
        if ModelValue != Document.brep and len(ModelValue.bodies) == 1:
            ModelValue, _ = LinkLocalBody(
                ModelValue, Document.bodies[0].id, Document.bodies[0].topology
            )
        if ModelValue != Document.brep:
            raise ValueError("public geometry differs from the selected native local body")
    Attributes = ReadBodyAttrs(NodesValue, NodesValue[TreeValue.BodyIndex])
    LabelValue, OwnerValue = ReadLocalLabel(
        NodesValue, Attributes, AtomValue, FeatureId, GroupKey
    )
    return BodyNameGraph(
        LinkValue,
        NodesValue,
        TreeValue,
        AtomValue,
        FeatureId,
        LabelValue,
        OwnerValue == "authored_atom_and_kernel",
        KLocalBodyStream,
        len(LocalStream),
        LocalStoreKey=GroupKey,
        LocalNameOwner=OwnerValue,
    )
