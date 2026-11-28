from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmChild import (
    CheckAsmChild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylPlan import (
    CheckCylPlan,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylSketch import (
    CheckCylSketch,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylWire import (
    CheckCylWire,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.ReadCylRims import (
    ReadCylRims,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import (
    PickCylFace,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import (
    ReadCylAttr,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import (
    ReadCylNodes,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import (
    ReadCylOwner,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import (
    ReadCylWords,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# generated mate ownership joins a real kernel face and stamp to the live generated part graph
def ReadMintedCyl(ChildValue: PartCandidate, FaceTag: int) -> CylFaceBuild:
    CheckAsmChild(ChildValue)
    ArchiveValue = SldprtArchive.from_bytes(ChildValue.BytesValue)
    if (
        ArchiveValue.format_version != 4
        or ArchiveValue.streams != ChildValue.StreamsValue
    ):
        raise ValueError(
            "concentric child streams differ from its complete generated file"
        )
    CheckCylWire(ChildValue)
    NodesValue = ReadCylNodes(ArchiveValue)
    FaceValue, Carrier, BodyValue = PickCylFace(NodesValue)
    AtomName = "ATOM_ID_2001"
    TagName = "SWEntUnchanged"
    AtomValue = ReadBodyScalar(
        NodesValue,
        {AtomName: ReadCylAttr(NodesValue, BodyValue, AtomName)},
        AtomName,
        1,
    )
    TagWord = ReadBodyScalar(
        NodesValue, {TagName: ReadCylAttr(NodesValue, FaceValue, TagName)}, TagName, 0
    )
    if (
        type(FaceTag) is not int
        or not 0 < FaceTag <= 0xFFFF
        or TagWord >> 16 & 0xFFFF != FaceTag
    ):
        raise ValueError("concentric face tag differs from its minted kernel owner")
    LinkValue = NativeLink(
        ChildValue.ConfigValue,
        ChildValue.ResolvedValue,
        ReadNodeName(ChildValue.CurrentConfig),
        "Contents/Config-0",
    )
    FeatureValue, ArcMarker = ReadCylOwner(LinkValue, AtomValue)
    FeatureId = FieldInt(FeatureValue.FieldsValue, "f08")
    CreatedAt = DatumTime(ChildValue.HeaderValue, FeatureId)
    EpochValue = SignedStamp(CreatedAt)
    if (
        FeatureValue is not ChildValue.BossValue.FeatureValue
        or ChildValue.ConfigValue.HeaderValue is not ChildValue.HeaderValue
        or ReadCylWords(NodesValue, FaceValue)
        != (74, FeatureId, EpochValue, 0, ArcMarker)
    ):
        raise ValueError(
            "concentric lateral face lacks its actual generating circle owner"
        )
    CheckCylSketch(ChildValue, LinkValue, ArcMarker)
    RimsValue, Selectors = ReadCylRims(
        NodesValue, FaceValue, Carrier, FeatureId, EpochValue
    )
    Radius = CheckCylPlan(ChildValue, Carrier, RimsValue)
    return CylFaceBuild(
        ReadXmtVector(Carrier, "pvec"),
        ReadXmtVector(Carrier, "axis"),
        Radius,
        RimsValue,
        Selectors,
        FeatureId,
        CreatedAt,
        ArcMarker,
        FaceValue.Integer("node_id"),
        FaceTag,
        AtomValue,
    )
