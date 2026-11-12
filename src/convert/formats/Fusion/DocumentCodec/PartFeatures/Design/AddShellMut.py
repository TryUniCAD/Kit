from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddPickMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec


def AddShellMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, RoofTag: int
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, ShellSpec):
        raise ValueError("Fusion part shell authoring requires a shell feature")
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcShellFeature", None)
    Cache: dict[str, object] = {"cachedEntityId": RoofTag, "scope": PartScope(Author)}
    AddPickMut(Author, Prefix, RoofRecipe(Stage.Before), 16, "ETCachedTopology", Cache)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    AddParamMut(
        Author, Prefix + "amount", MainRole, "innerThickness", Feature.ThicknessMm, "mm"
    )
    Author.Change(MainRole, rParamInnerThickness=Author.Reference(Prefix + "amount"))
    return [Prefix + NameValue for NameValue in ("target", "pick", "amount")]
