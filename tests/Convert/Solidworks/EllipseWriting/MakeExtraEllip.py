from xml.etree.ElementTree import Element as XmlElement, fromstring as ParseXml

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileMut import (
    MakeProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)
from convert.adapters.solidworks.Container.Cmgr import KConfigManagerStream
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
    KeywordsStream,
)


# a second real profile tests strict history ownership without using a saved part
def MakeExtraEllip(Candidate: EllipsePart) -> tuple[bytes, int]:
    ConfigValue, GraphValue = Candidate.ConfigValue, Candidate.ResolvedValue
    StreamValues = Candidate.StreamsValue
    VersionValue = ConfigValue.VersionValue
    HeaderValue = ConfigValue.HeaderValue
    TopHeader = ReadHeaderGraph(StreamValues["Header2"], VersionValue)
    ManagerValue = ReadCmgrMut(
        StreamValues[KConfigManagerStream], VersionValue
    ).RootValue
    Allocator = PersistentIds(FieldInt(HeaderValue.FieldsValue, "f08"))
    FrontValue = next(
        NodeValue
        for NodeValue in GraphValue.RootsValue
        if NodeValue is not None and ReadNodeName(NodeValue) == "Front Plane"
    )
    Extra = MakeProfileMut(
        "ExtraProfile",
        ConfigValue.RootValue,
        FrontValue,
        "z",
        PolygonInput(((0.002, 0.001), (0.012, 0.002), (0.005, 0.013)), VersionValue),
        FeatureTarget(2026306, 370108),
        Allocator,
    ).ProfileValue
    SetCfgStampMut(
        RequireNode(ManagerValue.FieldsValue["f360"], "moPartConfiguration_c"),
        Allocator,
    )
    HeaderValue.FieldsValue["f08"] = Allocator.NextValue
    TopHeader.FieldsValue["f08"] = Allocator.NextValue
    ConfigBytes, UpdatedConfig = WriteConfigMut(
        ConfigValue.RootValue, VersionValue, HeaderValue
    )
    Resolved, _ = WriteResolMut(
        (*GraphValue.RootsValue[:-1], Extra, GraphValue.RootsValue[-1]),
        GraphValue.ExtraFields,
        VersionValue,
        UpdatedConfig.MapValue,
        GraphValue.ContextValue,
        ReplayEllipses=True,
    )
    Keywords = ParseXml(StreamValues[KeywordsStream][1:])
    Keywords.insert(
        len(Keywords) - 1,
        XmlElement(
            "Sketch",
            {
                "id": str(FieldInt(Extra.FieldsValue, "f08")),
                "Name": "ExtraProfile",
                "Type": "moProfileFeature_c",
            },
        ),
    )
    Payload = BuildSldprt(
        dict(StreamValues)
        | {
            "Header2": WriteHeadGraph(TopHeader, VersionValue),
            KConfigStream + "-ModelHeader": WriteHeadGraph(HeaderValue, VersionValue),
            KConfigStream: ConfigBytes,
            KConfigManagerStream: WriteCmgrMut(ManagerValue, VersionValue),
            KResolvedFeaturesStream: Resolved,
            KeywordsStream: FrameKeywords(Keywords, False),
        },
        FormatVersion=4,
    )
    return Payload, Allocator.NextValue


# the serialized headers and active configuration must include the actual extra profile allocations
def CheckExtraIds(Payload: bytes, NextValue: int) -> None:
    Archive = SldprtArchive.from_bytes(Payload)
    for StreamName in ("Header2", KConfigStream + "-ModelHeader"):
        HeaderValue = ReadHeaderGraph(Archive.require(StreamName), 19000)
        assert FieldInt(HeaderValue.FieldsValue, "f08") == NextValue
    ManagerValue = ReadCmgrMut(Archive.require(KConfigManagerStream), 19000).RootValue
    ConfigValue = RequireNode(ManagerValue.FieldsValue["f360"], "moPartConfiguration_c")
    assert FieldInt(ConfigValue.FieldsValue, "f85c") == NextValue - 1
