from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def LinkCornerMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    if isinstance(Stage.Feature, FilletSpec):
        Author.Allocate(Prefix + "data", "DcFilletEdgeData")
        Author.Change(
            Prefix + "data",
            connectedEdgeRef=Reference(Prefix + "target"),
            radiusValue=Reference(Prefix + "amount"),
            tangencyWeight=Reference(Prefix + "weight"),
        )
        Author.Change(MainRole, filletEdgeData=[Reference(Prefix + "data")])
        return
    Feature = Stage.Feature
    Extra: dict[str, object] = {}
    if isinstance(Feature, ChamferSpec) and Feature.SecondMm > 0:
        Extra = dict(chamferType=2, chamferDistanceTwoParam=Reference(Prefix + "other"))
    elif isinstance(Feature, ChamferSpec) and Feature.AngleDegrees > 0:
        Extra = dict(chamferType=3, chamferAngleParam=Reference(Prefix + "other"))
    Author.Change(
        Prefix + "data",
        chamferDistanceOneParam=Reference(Prefix + "amount"),
        rInputEdgesRef=Reference(Prefix + "target"),
        **Extra,
    )
    Author.Change(
        MainRole,
        rChamferData=[Reference(Prefix + "data")],
        primaryIDRowIndexMap=[{"key": 1, "value": 1}],
    )
