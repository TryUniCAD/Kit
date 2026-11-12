from dataclasses import replace as ReplaceValue
from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofFaceRecipe,
    RoofRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    AddTargetMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddFaceRefMut,
    AddPlaceMut,
    AddThroughMut,
    TopologyCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.CheckHole import IsBored
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage

KThroughNote = "SavedHoleDepthInNonDistanceExtentsCase"


def HoleSpot(Stage: PartStage, Feature: HoleSpec) -> dict[str, float]:
    Ceiling = Stage.Before.Slabs[-1].UpperCm
    return {
        "x": Feature.CenterMm[0] / 10.0,
        "y": Feature.CenterMm[1] / 10.0,
        "z": Ceiling,
    }


def AddSizesMut(Author: AuthorState, Prefix: str, Feature: HoleSpec) -> list[str]:
    Owner = Prefix + "feature"
    Roles: list[str] = []
    if Feature.DepthMm:
        AddParamMut(Author, Prefix + "depth", Owner, "HoleDepth", Feature.DepthMm, "mm")
        Roles.append(Prefix + "depth")
    Width = Feature.DiameterMm
    AddParamMut(Author, Prefix + "diameter", Owner, "HoleDiameter", Width, "mm")
    TipValue = (180.0, "180 deg") if Feature.DepthMm else (118.0, "118.0 deg")
    AddParamMut(
        Author,
        Prefix + "tip",
        Owner,
        "TipAngle",
        Radians(TipValue[0]),
        "deg",
        TipValue[1],
    )
    Roles.extend((Prefix + "diameter", Prefix + "tip"))
    if IsBored(Feature):
        BoreDepth, BoreWidth = Feature.BoreDepthMm, Feature.BoreDiameterMm
        AddParamMut(Author, Prefix + "bore_depth", Owner, "CBDepth", BoreDepth, "mm")
        AddParamMut(Author, Prefix + "bore_width", Owner, "CBDiameter", BoreWidth, "mm")
        Roles.extend((Prefix + "bore_depth", Prefix + "bore_width"))
    return Roles


def AddHolePlaceMut(
    Author: AuthorState, Prefix: str, Stage: PartStage, TagSet: tuple[int, int, int]
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, HoleSpec):
        raise ValueError("Fusion hole authoring requires a hole feature")
    Reference = Author.Reference
    SpotValue = HoleSpot(Stage, Feature)
    Plane = {"x": 0.0, "y": 0.0}
    AddFaceRefMut(
        Author, Prefix, "spot_face", RoofFaceRecipe(Stage.Before), (33, TagSet[1])
    )
    Fields: dict[str, object] = dict(point3d=SpotValue, refType=6, param=Plane)
    Fields.update(dataRefs=[Reference(Prefix + "spot_face")])
    AddPlaceMut(Author, Prefix, ("spot", "DRPoint"), Fields)
    Direction = {"x": 0.0, "y": 0.0, "z": 1.0}
    LineValue = {"pointOnLine": SpotValue, "parametricDirection": Direction}
    Fields = dict(
        axisTrackType=8, line3d=LineValue, param=Plane, refType=19, resizeType=0
    )
    AddPlaceMut(Author, Prefix, ("axis", "DRVector"), Fields)
    AddFaceRefMut(
        Author, Prefix, "axis_face", RoofRecipe(Stage.Before), (17, TagSet[0])
    )
    Author.Change(Prefix + "axis", dataRefs=[Reference(Prefix + "axis_face")])
    return [
        Prefix + NameValue for NameValue in ("spot_face", "spot", "axis", "axis_face")
    ]


def AddHoleMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: tuple[int, int, int]
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, HoleSpec):
        raise ValueError("Fusion hole authoring requires a hole feature")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcHoleFeature", None)
    Label = ReplaceValue(Stage.Before.BodyLabel, Merged=())
    Children = AddTargetMut(Author, Prefix, Label)
    Author.Change(Prefix + "target", trackingType=4)
    Children += AddHolePlaceMut(Author, Prefix, Stage, TagSet)
    Children += AddSizesMut(Author, Prefix, Feature)
    Extent = [] if Feature.DepthMm else AddThroughMut(Author, Prefix, Label, TagSet[1])
    AddNodeMut(Author, Prefix + "tool", "DcHoleToolBody", MainRole)
    TopologyCache(Author, Prefix + "tool_cache", TagSet[2])
    Author.Change(
        Prefix + "tool",
        rHoleFeature=Reference(MainRole),
        toolbodyCaches=[Reference(Prefix + "tool_cache")],
    )
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=[], tagId=1)
    LinkHoleMut(Author, Prefix, Feature, Extent)
    return Children + Extent + [Prefix + "tool"]


def LinkHoleMut(
    Author: AuthorState, Prefix: str, Feature: HoleSpec, Extent: list[str]
) -> None:
    Reference = Author.Reference
    Bored = IsBored(Feature)
    Author.Change(
        Prefix + "feature",
        holeType=1 if Bored else 0,
        bThroughAll=not Feature.DepthMm,
        rHoleDepth=Reference(Prefix + "depth" if Feature.DepthMm else None),
        rHoleDiameter=Reference(Prefix + "diameter"),
        rTipAngle=Reference(Prefix + "tip"),
        rCBDepth=Reference(Prefix + "bore_depth" if Bored else None),
        rCBDiameter=Reference(Prefix + "bore_width" if Bored else None),
        rDRMultipleOrigins=[Reference(Prefix + "spot")],
        rDRNormal=Reference(Prefix + "axis"),
        rHoleToolBody=Reference(Prefix + "tool"),
        rToEntityRefs=[Reference(Extent[0])] if Extent else [],
    )
    if not Feature.DepthMm:
        NoteValue = {"name": KThroughNote, "metatype": "IntrinsicMetaTypedouble"}
        Author.FindEntity(Prefix + "feature").NamedPairs = [dict(NoteValue, value=1.0)]
