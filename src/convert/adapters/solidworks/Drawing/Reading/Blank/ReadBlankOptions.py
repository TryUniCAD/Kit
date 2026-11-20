from uuid import UUID
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import (
    DrawFolders,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode as NeedNode,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadConceptName import (
    ReadConceptName as ReadName,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText as ReadText,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids as Children,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.One import OnlyItem
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankStyle import (
    ReadBlankStyle,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankUnits import (
    ReadBlankUnits,
)


# drawing presentation and independent block identity must come from their actual modeled owners
def ReadDrawOpts(Model: ArchiveNode, CreatedAt: int, Language: int) -> DrawDocOptions:
    Value = Fields(Model)
    Sheet = NeedNode(Value["f1430"], "moDrSheet")
    SheetFields = Sheet.FieldsValue
    Members = Children(Model)
    Names: dict[str, str] = {}
    for KindValue in (
        "moDetailCabinet_c",
        "moDocsFolder_c",
        "moCommentsFolder_c",
        "moBlockFolder_c",
        "moInkMarkupFolder_c",
        "moMarkupCommentFolder_c",
    ):
        Names[KindValue] = ReadName(
            OnlyItem(
                tuple(
                    Member
                    for Member in Members
                    if Member.ClassValue.NameValue == KindValue
                )
            )
        )
    Supports = Children(Sheet)
    Require(
        tuple(ItemValue.ClassValue.NameValue for ItemValue in Supports)
        == ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c"),
        "blank sheet support order differs",
    )
    Target = FeatureTarget(
        Integer(SheetFields["f2b4"]),
        Integer(SheetFields["f2ac"]),
        Integer(SheetFields["f2b0"]),
        Integer(SheetFields["f300"]),
        Integer(SheetFields["f301"]),
    )
    Identity = NeedNode(Value["fe80"], "moSketchBlockMgr_c").FieldsValue["f380"]
    Require(
        type(Identity) is bytes and len(Identity) == 16,
        "blank block identity is invalid",
    )
    Require(
        Integer(Value["f1444"]) in (256, 257),
        "blank auto dimension text state has extra flags",
    )
    return DrawDocOptions(
        ReadName(Model),
        ReadText(SheetFields["f3d0"]),
        SheetNames(*(ReadName(ItemValue) for ItemValue in Supports)),
        DrawFolders(
            *(
                Names[KindValue]
                for KindValue in (
                    "moDetailCabinet_c",
                    "moDocsFolder_c",
                    "moCommentsFolder_c",
                    "moBlockFolder_c",
                    "moInkMarkupFolder_c",
                    "moMarkupCommentFolder_c",
                )
            )
        ),
        ReadBlankStyle(Model, Language),
        ReadBlankUnits(Model),
        Target,
        CreatedAt,
        UUID(bytes_le=CastValue(bytes, Identity)),
        bool(Integer(Value["f1444"]) & 1),
    )
