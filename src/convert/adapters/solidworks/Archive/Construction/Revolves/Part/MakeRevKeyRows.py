from math import degrees as Degrees

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ThinWallPlan import (
    ThinWallPlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# only the measured active wall drivers appear in the keyword feature row
def MakeThinKeyDims(
    AngleValue: KeywordDim, WallValue: ThinWallPlan
) -> tuple[KeywordDim, ...]:
    FirstValue, SecondValue = WallValue.LengthValues
    FirstDim = KeywordDim("D3", 1000 * FirstValue, None)
    if WallValue.ModeValue == 3:
        return AngleValue, KeywordDim("D4", 1000 * SecondValue, None), FirstDim
    return FirstDim, AngleValue


# feature and consumed sketch order follow their native ordinary or thin parent relationship
def MakeRevKeyRows(
    ProfileValue: ArchiveNode, FeatureValue: ArchiveNode, PlanValue: RevolvePlan
) -> tuple[KeywordFeature, KeywordFeature]:
    SketchRow = KeywordFeature(
        FieldInt(ProfileValue.FieldsValue, "f08"),
        ReadNodeName(ProfileValue),
        None,
        "Sketch",
        (),
        (),
        True,
        None,
    )
    AngleValue = KeywordDim("D1", Degrees(PlanValue.AngleValue), "degree")
    WallsValue = PlanValue.ThinWalls
    KindValue = "Revolve-Thin" if WallsValue is not None else "Revolve"
    DimsValue: tuple[KeywordDim, ...] = (AngleValue,)
    if WallsValue is not None:
        DimsValue = MakeThinKeyDims(AngleValue, WallsValue)
    elif PlanValue.AgainstAngle is not None:
        Secondary = KeywordDim("D2", Degrees(PlanValue.AgainstAngle), "degree")
        DimsValue = (
            (AngleValue, Secondary) if PlanValue.IsReverse else (Secondary, AngleValue)
        )
    FeatureRow = KeywordFeature(
        FieldInt(FeatureValue.FieldsValue, "f08"),
        ReadNodeName(FeatureValue),
        KindValue,
        "Feature",
        DimsValue,
        (),
        None,
        None,
    )
    return (
        (FeatureRow, SketchRow) if WallsValue is not None else (SketchRow, FeatureRow)
    )
