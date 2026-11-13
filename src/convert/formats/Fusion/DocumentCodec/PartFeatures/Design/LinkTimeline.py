from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


def TimelineOwners(
    Author: AuthorState, Stages: tuple[PartStage, ...]
) -> list[tuple[str, tuple[int, ...]]]:
    First = Author.Policy.FirstOperationId
    Owners: list[tuple[str, tuple[int, ...]]] = []
    if Author.SpecValue.ProfileKind != "part":
        Owners = [("dc_sketch", (First,)), ("dc_extrude", (First + 1, First + 2))]
    for Index, Stage in enumerate(Stages):
        Prefix = "f" + str(Index + 1) + "_"
        if isinstance(Stage.Feature, ExtrudeSpec):
            Owners.append((Prefix + "dc_sketch", Stage.Operations[:1]))
            Owners.append((Prefix + "feature", Stage.Operations[1:]))
            continue
        if not isinstance(Stage.Feature, (PatternSpec, CircularSpec, MirrorSpec)):
            Owners.append((Prefix + "feature", Stage.Operations))
            continue
        Owners.append((Prefix + "feature", Stage.Operations[:1]))
        Owners.extend(
            (Prefix + "occ_" + str(Ordinal), (Operation,))
            for Ordinal, Operation in enumerate(Stage.Operations)
            if Ordinal
        )
    return Owners


def LinkSketches(Author: AuthorState, Stages: tuple[PartStage, ...]) -> None:
    Reference = Author.Reference
    Roles = [] if Author.SpecValue.ProfileKind == "part" else ["rectangle_sketch"]
    NextTag = Author.Policy.FirstSketchTag + 9
    for Index, Stage in enumerate(Stages):
        if Stage.Sketch is not None:
            Roles.append("f" + str(Index + 1) + "_sketch")
            NextTag = Stage.Sketch.NextTag
    if not Roles or (len(Roles) == 1 and Roles[0] == "rectangle_sketch"):
        return
    Author.Change(
        "sketches",
        highWaterMark=len(Roles),
        groupChildren=[Reference(RoleName) for RoleName in Roles],
    )
    Author.FindEntity("sketches").NamedPairs = MakeAttributes(crv_tag_id_idx=NextTag)
    Author.Change(
        "sketches_root",
        rootId="SketchesRoot",
        rooted=[Reference(RoleName) for RoleName in Roles],
    )


def LinkTimeline(Author: AuthorState, Stages: tuple[PartStage, ...]) -> None:
    Reference = Author.Reference
    Owners = TimelineOwners(Author, Stages)
    Author.Change(
        "creation_order",
        representationFeatures=[
            Reference(RoleName) for RoleName, _ in Owners if "_occ_" not in RoleName
        ],
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
    IsPart = Author.SpecValue.ProfileKind == "part"
    Counts = {} if IsPart else {"DcExtrudeFeatureMetaType": 1, "DcSketchMetaType": 1}
    for Stage in Stages:
        NameValue = FamilyOf(Stage.Feature).ClassName + "MetaType"
        Counts[NameValue] = Counts.get(NameValue, 0) + 1
        if isinstance(Stage.Feature, ExtrudeSpec):
            Counts["DcSketchMetaType"] = Counts.get("DcSketchMetaType", 0) + 1
    Author.Change(
        "fragment",
        featureIndexMap=[
            {"key": KeyValue, "value": Counts[KeyValue]} for KeyValue in sorted(Counts)
        ],
    )
    Author.Change("component", operationSeedId=Owners[-1][1][-1] + 1)
    LinkSketches(Author, Stages)
