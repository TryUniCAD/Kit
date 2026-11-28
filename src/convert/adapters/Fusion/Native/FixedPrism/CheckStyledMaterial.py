from uuid import UUID as ReadUuid

from convert.adapters.Fusion.Native.FixedPrism.CheckStyledRecipe import (
    KRoofNormal,
    KSideNormals,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.Formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset


# the design map and native owner must name one attached appearance before graphics can corroborate it
def CheckStyleMat(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    History: JournalModel,
    Reference: NativeNode,
    Normal: KJournalVector,
) -> None:
    FaceTag = TextValue(Reference.Fields["visualMaterialTag"])
    MaterialValue = Reference.Fields["visualMaterial"]
    Entries = MappingItems(Context.BodyNode.Fields["faceVisualMaterialByAttrTagID"])
    if (
        Reference.ClassName != "VMBrepRef"
        or len(Entries) != 1
        or Entries[0].First != FaceTag
        or Entries[0].Second != MaterialValue
        or Normal not in (*KSideNormals, KRoofNormal)
    ):
        raise ValueError(
            "Fusion styled Design face assignment disagrees with its owner"
        )

    FaceFields = ObjectFields(MaterialValue)
    Physical = ObjectFields(Context.BodyNode.Fields["physicalMaterial"])
    Visual = ObjectFields(Context.BodyNode.Fields["visualMaterial"])
    Manager = Graph.Resolve(Physical["ProteinAssetManager"])
    FaceId = TextValue(FaceFields["assetReference"])
    VisualId = TextValue(Visual["assetReference"])
    PhysicalId = TextValue(Physical["assetReference"])
    if (
        Manager.ClassName != "ProteinAssetManager"
        or Graph.Resolve(FaceFields["ProteinAssetManager"]) != Manager
        or FaceFields["libraryID"] != Visual["libraryID"]
        or FaceFields["libraryID"] != Physical["libraryID"]
        or FaceFields["proteinMaterialID"] != Visual["proteinMaterialID"]
        or any(
            FaceFields[FieldKey] != Visual[FieldKey]
            for FieldKey in (
                "CustomizedColor",
                "UseCustomizedColor",
                "name",
                "proteinMaterialRotation",
                "proteinMaterialScale",
            )
        )
        or str(ReadUuid(FaceId)).casefold() != FaceId.casefold()
        or len({FaceId.casefold(), VisualId.casefold(), PhysicalId.casefold()}) != 3
    ):
        raise ValueError("Fusion styled face lacks its own attached Protein appearance")

    _ = ReadMaterial(Graph, Context, Model)
    Parts = tuple(
        MatPart.Package
        for MatPart in Model.Materials
        if MatPart.Name
        == "ProteinAssets.BlobParts/" + TextValue(Manager.Fields["partName"])
    )
    if len(Parts) != 1:
        raise ValueError("Fusion styled Protein package is not unique")
    CheckFaceAssets(Parts[0].Assets, FaceId)

    if Model.Graphics is not None:
        CheckSceneRefs(Graph, Model.Graphics)
        CheckFaceLeaves(Model.Graphics, Context, History, Normal, VisualId, FaceId)


# both saved protein representations must belong to the uuid and carry the same resolved color
def CheckFaceAssets(Assets: tuple[MaterialAsset, ...], FaceId: str) -> None:
    Matches = tuple(
        Asset for Asset in Assets if Asset.InstanceId in (FaceId, FaceId + "_Post2015")
    )
    Index = {Asset.InstanceId: Asset for Asset in Matches}
    if len(Matches) != 2 or len(Index) != 2:
        raise ValueError(
            "Fusion styled Protein appearance pair is missing or ambiguous"
        )
    Basic = Index[FaceId]
    Modern = Index[FaceId + "_Post2015"]
    BasicColors = tuple(
        Entry.Value
        for Entry in Basic.Properties
        if Entry.FieldName == "generic_diffuse"
    )
    ModernColors = tuple(
        Entry.Value for Entry in Modern.Properties if Entry.FieldName == "metal_f0"
    )
    if (
        Basic.AssetRole != "materialappearance"
        or Modern.AssetRole != Basic.AssetRole
        or Basic.SchemaName != "GenericSchema"
        or Modern.SchemaName != "PrismMetalSchema"
        or len(BasicColors) != 1
        or not isinstance(BasicColors[0], ColorValue)
        or ModernColors != BasicColors
    ):
        raise ValueError("Fusion styled Protein appearance color or schema disagrees")


# the leaf bounds associate the independently proven face role without trusting display order or qualifier values
def CheckFaceLeaves(
    Scene: GraphicScene,
    Context: ExtrudeContext,
    History: JournalModel,
    Normal: KJournalVector,
    VisualId: str,
    FaceId: str,
) -> None:
    Target = EntityRef(Context.BodyNode.SegmentId, Context.BodyNode.ObjectId)
    WorldValue = ReadFaceWorld(Scene, Target, VisualId)
    CheckLeafStyles(
        WorldValue.FaceNodes, Target, FaceId, ReadFaceBounds(History, Normal)
    )


# shared face appearance must resolve on the display group for the actual design body
def ReadFaceWorld(Scene: GraphicScene, Target: EntityRef, VisualId: str) -> BrepWorld:
    Groups = tuple(
        Group
        for Entry in Scene.Objects
        if isinstance(Group := Entry.Value, GroupValue)
        and isinstance(Group.WorldValue, BrepWorld)
    )
    if len(Groups) != 1:
        raise ValueError("Fusion styled scene requires one body display owner")
    (Group,) = Groups
    World = Group.WorldValue
    RootData = Group.NodeData.DataValue
    if (
        not isinstance(World, BrepWorld)
        or Group.Matrix is not None
        or RootData is None
        or RootData.EntityLink != Target
        or World.FaceGroup is None
        or World.FaceGroup.Matrix is not None
        or len(World.FaceNodes) != 6
    ):
        raise ValueError("Fusion styled body display owner disagrees")
    FaceGroup = World.FaceGroup.NodeData.DataValue
    ExpectedBase: SceneSet = SceneSet(
        2,
        FlagsValue=32,
        Attributes=(
            GraphicAttr(
                "FPrioritizedProteinAttribute",
                0,
                False,
                (
                    FieldValue("AssetReference", VisualId),
                    FieldValue("Category", 0),
                ),
            ),
        ),
    )
    if (
        FaceGroup is None
        or FaceGroup.EntityLink != Target
        or FaceGroup.Attributes != ExpectedBase
    ):
        raise ValueError("Fusion styled display baseline appearance disagrees")

    return World


# live cuboid bounds identify the styled face without relying on display order
def ReadFaceBounds(History: JournalModel, Normal: KJournalVector) -> tuple[float, ...]:
    Table = MakeLiveTable(History, None)
    (BodyRef,) = tuple(
        SlotId
        for SlotId in Table.LiveSlots
        if isinstance(Table.Entities[SlotId], BodyNode)
    )
    BodyValue = ReadPlacedBody(Table, BodyRef)
    RoleAxis = next(Index for Index, Value in enumerate(Normal) if Value)
    Coordinates = tuple(zip(*BodyValue.PointsCm, strict=True))
    Lower = tuple(min(Values) for Values in Coordinates)
    Upper = tuple(max(Values) for Values in Coordinates)
    Plane = Upper[RoleAxis] if Normal[RoleAxis] > 0 else Lower[RoleAxis]
    return (
        *Lower[:RoleAxis],
        Plane,
        *Lower[RoleAxis + 1 :],
        *Upper[:RoleAxis],
        Plane,
        *Upper[RoleAxis + 1 :],
    )


# leaf overrides must agree uniquely with the proven body and face role
def CheckLeafStyles(
    FaceNodes: tuple[LodValue, ...],
    Target: EntityRef,
    FaceId: str,
    Expected: tuple[float, ...],
) -> None:
    ExpectedStyle: SceneSet = SceneSet(
        2,
        FlagsValue=32,
        Attributes=(
            GraphicAttr(
                "FProteinEffectAttribute",
                3,
                True,
                (FieldValue("AssetReference", FaceId),),
            ),
        ),
    )
    Qualifiers: set[float] = set()
    StyledCount = 0
    for FaceLeaf in FaceNodes:
        FaceNode = FaceLeaf.NodeData.DataValue
        if (
            FaceNode is None
            or FaceNode.EntityLink != Target
            or FaceNode.Qualifier in Qualifiers
        ):
            raise ValueError("Fusion styled display leaf lacks unique body ownership")
        Qualifiers.add(FaceNode.Qualifier)
        if FaceNode.Attributes == SceneSet(0):
            continue
        if FaceNode.Attributes != ExpectedStyle:
            raise ValueError("Fusion styled display leaf has an unexpected appearance")
        StyledCount += 1
        SameNumbers(FaceLeaf.Bounds, Expected)
    if StyledCount != 1:
        raise ValueError("Fusion styled display appearance is missing or duplicated")
