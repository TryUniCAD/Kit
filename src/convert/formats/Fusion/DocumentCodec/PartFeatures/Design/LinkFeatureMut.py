from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def LinkFeatureMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, Children: list[str]
) -> None:
    Reference = Author.Reference
    Author.Change(
        Prefix + "feature",
        childNodes=[Reference(RoleName) for RoleName in Children],
        featureBaseName=FamilyOf(Stage.Feature).BaseName,
        featureUserName=Stage.Feature.FeatureName,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=Stage.StateId - 1,
        endModelHS=Stage.StateId,
        targetDataRefs=[Reference(Prefix + "target")],
    )
