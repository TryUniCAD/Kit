from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def LinkTimeline(Author: AuthorState, Stages: tuple[PartStage, ...]) -> None:
    Reference = Author.Reference
    First = Author.Policy.FirstOperationId
    Owners: list[tuple[str, tuple[int, ...]]] = [
        ("dc_sketch", (First,)),
        ("dc_extrude", (First + 1, First + 2)),
    ]
    Owners.extend(
        ("f" + str(Index + 1) + "_feature", Stage.Operations)
        for Index, Stage in enumerate(Stages)
    )
    Author.Change(
        "creation_order",
        representationFeatures=[Reference(RoleName) for RoleName, _ in Owners],
    )
    Author.Change(
        "feature_ids",
        enetityIdMap=[
            {"key": Author.Roles[RoleName], "value": list(Values)}
            for RoleName, Values in Owners
        ],
        featureIdMap=[
            {"key": Value, "value": Author.Roles[RoleName]}
            for RoleName, Values in Owners
            for Value in Values
        ],
    )
    Counts = {"DcExtrudeFeatureMetaType": 1, "DcSketchMetaType": 1}
    for Stage in Stages:
        NameValue = FamilyOf(Stage.Feature).ClassName + "MetaType"
        Counts[NameValue] = Counts.get(NameValue, 0) + 1
    Author.Change(
        "fragment",
        featureIndexMap=[
            {"key": KeyValue, "value": Counts[KeyValue]} for KeyValue in sorted(Counts)
        ],
    )
    Author.Change("component", operationSeedId=Owners[-1][1][-1] + 1)
