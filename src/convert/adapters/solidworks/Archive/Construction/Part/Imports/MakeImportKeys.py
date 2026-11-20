from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesGraph import (
    NotesGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# the local import keyword tree must follow actual allocated roots and their native names
def MakeImportKeys(
    SystemValue: PartSystem,
    FeatureValue: ArchiveNode,
    Timestamp: int,
    NotesValue: NotesGraph | None,
) -> bytes:
    ConfigValues = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"), ReadNodeName(NodeValue), ""
        )
        for NodeValue in SystemValue.ConfigValues
    )
    FeatureValues = tuple(
        KeywordFeature(
            FieldInt(NodeValue.FieldsValue, "f08"),
            ReadNodeName(NodeValue),
            "Imported" if NodeValue is FeatureValue else NodeValue.ClassValue.NameValue,
            "Feature",
            (),
            (),
            None,
            None,
        )
        for NodeValue in (*SystemValue.FeatureValues, FeatureValue)
    )
    if NotesValue is not None:
        FeatureValues = (
            *FeatureValues,
            *(
                KeywordFeature(
                    FieldInt(NodeValue.FieldsValue, "f08"),
                    ReadNodeName(NodeValue),
                    "Notes",
                    "Feature",
                    (),
                    (),
                    None,
                    None,
                )
                for NodeValue in (NotesValue.HeadValue, NotesValue.EndValue)
            ),
        )
    return MakeKeywords(
        ReadNodeName(SystemValue.RootValue), Timestamp, ConfigValues, FeatureValues
    )
