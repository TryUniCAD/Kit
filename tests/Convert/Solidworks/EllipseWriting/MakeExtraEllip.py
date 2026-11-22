from xml.etree.ElementTree import Element as XmlElement, fromstring as ParseXml

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
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KResolvedFeaturesStream,
    KeywordsStream,
)


# a second real profile tests strict history ownership without using a saved part
def MakeExtraEllip(Candidate: EllipsePart) -> bytes:
    ConfigValue, GraphValue = Candidate.ConfigValue, Candidate.ResolvedValue
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
        PolygonInput(((0.002, 0.001), (0.012, 0.002), (0.005, 0.013)), 19000),
        FeatureTarget(2026306, 370108),
        PersistentIds(FieldInt(ConfigValue.HeaderValue.FieldsValue, "f08")),
    ).ProfileValue
    Resolved, _ = WriteResolMut(
        (*GraphValue.RootsValue[:-1], Extra, GraphValue.RootsValue[-1]),
        GraphValue.ExtraFields,
        19000,
        ConfigValue.MapValue,
        GraphValue.ContextValue,
        ReplayEllipses=True,
    )
    Keywords = ParseXml(Candidate.StreamsValue[KeywordsStream][1:])
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
    return BuildSldprt(
        dict(Candidate.StreamsValue)
        | {
            KResolvedFeaturesStream: Resolved,
            KeywordsStream: FrameKeywords(Keywords, False),
        },
        FormatVersion=4,
    )
