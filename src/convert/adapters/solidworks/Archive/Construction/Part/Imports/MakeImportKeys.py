from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportKeyInput import (
    ImportKeyInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImpKeyNodes import (
    ReadImpKeyNodes,
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
    *,
    KeywordInput: ImportKeyInput | None = None,
) -> bytes:
    if KeywordInput is not None and type(KeywordInput) is not ImportKeyInput:
        raise TypeError("native import keywords require a typed index input")
    ConfigMaterial = KeywordInput.MaterialValue if KeywordInput is not None else ""
    ConfigValues = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"),
            ReadNodeName(NodeValue),
            ConfigMaterial,
        )
        for NodeValue in SystemValue.ConfigValues
    )
    if KeywordInput is not None:
        _, RowsValue, MaterialValue = ReadImpKeyNodes(
            SystemValue.RootValue, (*SystemValue.FeatureValues, FeatureValue)
        )
        if ConfigMaterial not in (None, MaterialValue):
            raise ValueError("import keyword material differs from its actual folder")
        return MakeKeywords(
            KeywordInput.TitleValue,
            KeywordInput.SavedAt,
            ConfigValues,
            RowsValue,
            CompactTags=True,
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
    ExplodedValue = SystemValue.RootValue.FieldsValue.get("f13f8")
    if ExplodedValue is not None:
        ManagerValue = ArchiveNode.RequireNode(ExplodedValue)
        FeatureValues = (
            *FeatureValues,
            KeywordFeature(
                FieldInt(ManagerValue.FieldsValue, "f08"),
                "",
                "Exploded Views",
                "Feature",
                (),
                (),
                None,
                None,
            ),
        )
    return MakeKeywords(
        ReadNodeName(SystemValue.RootValue), Timestamp, ConfigValues, FeatureValues
    )
