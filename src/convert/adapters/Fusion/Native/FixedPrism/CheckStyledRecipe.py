from itertools import product as GridPoints

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    MaterialAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofRecipe,
    SideRecipe,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import ReadFeatureTags

# the role order follows the counterclockwise positive horizontal profile used by the recipe builders
KSideNormals: tuple[KJournalVector, ...] = (
    (0.0, -1.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (-1.0, 0.0, 0.0),
)

# the cap roles distinguish the native roof selector from the unsupported floor case
KRoofNormal: KJournalVector = (0.0, 0.0, 1.0)

# the floor label is needed for side adjacency even when no floor selector is admitted
KFloorNormal: KJournalVector = (0.0, 0.0, -1.0)


# prism recipe bounds are derived only after validating the closed axis aligned body
def CuboidBounds(Table: LiveTable, BodyRef: int) -> KJournalVector:
    Shell = ReadPlacedBody(Table, BodyRef)
    if Shell.Placement is not None or len(Shell.FaceRefs) != 6:
        raise ValueError("Fusion styled recipe requires an unplaced cuboid")
    XAxis, YAxis, ZAxis = tuple(
        (min(Values), max(Values)) for Values in zip(*Shell.PointsCm, strict=True)
    )
    (LowerX, UpperX), (LowerY, UpperY), (LowerZ, UpperZ) = XAxis, YAxis, ZAxis
    if (
        (LowerX, LowerY, LowerZ) != (0.0, 0.0, 0.0)
        or min(UpperX, UpperY, UpperZ) <= 0.0
        or len(Shell.PointsCm) != 8
        or set(Shell.PointsCm) != set(GridPoints(XAxis, YAxis, ZAxis))
    ):
        raise ValueError(
            "Fusion styled recipe requires origin-anchored cuboid geometry"
        )
    return UpperX, UpperY, UpperZ


# each supported face role must have one physical boundary and one owned feature tag
def CuboidLabels(
    Table: LiveTable, BodyRef: int, MaterialTag: str
) -> tuple[dict[KJournalVector, FaceLabel], FaceLabel, KJournalVector]:
    FeatureTags = ReadFeatureTags(Table)
    Labels: dict[KJournalVector, FaceLabel] = {}
    FaceRefs: dict[KJournalVector, int] = {}
    for Boundary in ReadBodyFaces(Table, BodyRef):
        NormalX, NormalY, NormalZ = Boundary.Surface.Normal
        Normal = (
            (-NormalX, -NormalY, -NormalZ)
            if Boundary.Reversed
            else (NormalX, NormalY, NormalZ)
        )
        TagValue = FeatureTags.get(Boundary.FaceRef)
        if (
            Normal not in (*KSideNormals, KRoofNormal, KFloorNormal)
            or Normal in Labels
            or len(Boundary.BoundaryUses) != 4
            or TagValue is None
            or TagValue.ApproachId != 0
        ):
            raise ValueError("Fusion styled recipe requires six tagged cuboid faces")
        Labels[Normal] = FaceLabel(
            TagValue.PrimaryId, TagValue.OperationIds, TagValue.SecondaryId
        )
        FaceRefs[Normal] = Boundary.FaceRef
    BodyTag = FeatureTags.get(BodyRef)
    if BodyTag is None or BodyTag.ApproachId != 0:
        raise ValueError("Fusion styled recipe requires the owning cuboid feature tag")
    BodyLabel = FaceLabel(BodyTag.PrimaryId, BodyTag.OperationIds, BodyTag.SecondaryId)
    return Labels, BodyLabel, MaterialNormal(Table, FaceRefs, MaterialTag)


# a named material tag must resolve to one supported face of the verified body
def MaterialNormal(
    Table: LiveTable, FaceRefs: dict[KJournalVector, int], MaterialTag: str
) -> KJournalVector:
    Owners = tuple(
        StableRef(Table, Entity.Links.OwnerRef)
        for SlotId in Table.LiveSlots
        if isinstance(Entity := Table.Entities[SlotId], MaterialAttrib)
        and Entity.Tag == MaterialTag
    )
    Matches = tuple(
        Normal for Normal, FaceRef in FaceRefs.items() if Owners == (FaceRef,)
    )
    if len(Matches) != 1:
        raise ValueError("Fusion styled recipe does not name its material face owner")
    (Normal,) = Matches
    if Normal not in (*KSideNormals, KRoofNormal):
        raise ValueError("Unsupported Fusion styled cuboid face role")
    return Normal


# styled references must reproduce the entire bound recipe from the live cuboid and its owned tags
def CheckStylePick(
    History: JournalModel,
    MaterialTag: str,
    Recipe: RecipeValue,
) -> KJournalVector:
    Table = MakeLiveTable(History, None)
    Bodies = tuple(
        SlotId
        for SlotId in Table.LiveSlots
        if isinstance(Table.Entities[SlotId], BodyNode)
    )
    if len(Bodies) != 1:
        raise ValueError("Fusion styled recipe requires one live cuboid body")
    (BodyRef,) = Bodies
    UpperX, UpperY, UpperZ = CuboidBounds(Table, BodyRef)
    Labels, BodyLabel, Normal = CuboidLabels(Table, BodyRef, MaterialTag)
    Corners = ((0.0, 0.0), (UpperX, 0.0), (UpperX, UpperY), (0.0, UpperY))
    SideLoop = tuple(
        LineSpan(Corners[Index - 1], Corners[Index % len(Corners)], Labels[SideRole])
        for Index, SideRole in enumerate(KSideNormals, 1)
    )
    SolidSlab = PrismSlab(
        0.0, UpperZ, (SideLoop,), Labels[KFloorNormal], Labels[KRoofNormal]
    )
    Solid = PrismSolid((SolidSlab,), BodyLabel)
    Expected = (
        RoofRecipe(Solid)
        if Normal == KRoofNormal
        else SideRecipe(Solid, KSideNormals.index(Normal))
    )
    if Expected != Recipe:
        raise ValueError(
            "Fusion styled cuboid face recipe disagrees with live topology"
        )
    return Normal
