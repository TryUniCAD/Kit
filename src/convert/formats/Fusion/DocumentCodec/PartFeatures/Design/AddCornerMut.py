from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddPickMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    CornerRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def CornerCache(Stage: PartStage, CornerCm: tuple[float, float]) -> dict[str, object]:
    Lower = Stage.Before.Slabs[0].LowerCm
    Height = Stage.Before.Slabs[-1].UpperCm - Lower
    return {
        "rCachedGeometry": dict(
            startPoint={"x": CornerCm[0], "y": CornerCm[1], "z": Lower},
            displacement={"x": 0.0, "y": 0.0, "z": Height},
        )
    }


def AddBevelMut(
    Author: AuthorState, Prefix: str, Feature: ChamferSpec
) -> tuple[str, ...]:
    MainRole = Prefix + "feature"
    Amount = Feature.DistanceMm
    if Feature.SecondMm > 0:
        AddParamMut(Author, Prefix + "amount", MainRole, "Distance 1", Amount, "mm")
        Other = Feature.SecondMm
        AddParamMut(Author, Prefix + "other", MainRole, "Distance 2", Other, "mm")
        return ("other",)
    AddParamMut(Author, Prefix + "amount", MainRole, "Distance", Amount, "mm")
    if Feature.AngleDegrees <= 0:
        return ()
    Angle = Feature.AngleDegrees
    Expression = ExprText(Angle) + " deg"
    AddParamMut(
        Author,
        Prefix + "other",
        MainRole,
        "Rotate Angle",
        Radians(Angle),
        "deg",
        Expression,
    )
    return ("other",)


def AddCornerMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, (FilletSpec, ChamferSpec)):
        raise ValueError("Fusion part corner feature requires a fillet or chamfer")
    CornerCm = (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0)
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, FamilyOf(Feature).ClassName, None)
    Recipe = CornerRecipe(Stage.Before, CornerCm)
    AddPickMut(
        Author, Prefix, Recipe, 8, "ETCachedLineSeg3d", CornerCache(Stage, CornerCm)
    )
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Allocate(Prefix + "seed", "BrepProgenitor", NamedPairs=[])
    Author.Allocate(Prefix + "seed_recipe", "ASMRecipe", Fields={"m_Recipe": Recipe})
    Author.Change(
        Prefix + "seed", m_brepRecipe=Author.Reference(Prefix + "seed_recipe")
    )
    Author.Change(
        Prefix + "progenitors",
        ProgenitorTagVec=[{"first": Author.Reference(Prefix + "seed"), "second": 1}],
        tagId=2,
    )
    if isinstance(Feature, FilletSpec):
        AddParamMut(Author, Prefix + "weight", MainRole, "TangencyWeight", 1.0, "")
        AddParamMut(
            Author, Prefix + "amount", MainRole, "Radius", Feature.RadiusMm, "mm"
        )
        return [
            Prefix + NameValue for NameValue in ("target", "pick", "weight", "amount")
        ]
    Extra = AddBevelMut(Author, Prefix, Feature)
    AddNodeMut(Author, Prefix + "data", "DcChamferData", MainRole, False)
    Roles = ("target", "pick", "amount", *Extra, "data")
    return [Prefix + NameValue for NameValue in Roles]
