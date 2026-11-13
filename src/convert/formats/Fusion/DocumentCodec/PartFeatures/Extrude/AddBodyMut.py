from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def BodyTagInfo(
    Author: AuthorState, Count: int, Operation: int
) -> list[dict[str, object]]:
    Labels = tuple(str(Index + 3).encode("ascii") for Index in range(Count))
    Offsets = [0]
    for Label in Labels:
        Offsets.append(Offsets[-1] + len(Label))
    return [
        Author.MakeGroup(
            "FeatureTagInfoValue",
            dict(
                facePrimIdData=list(b"".join(Labels)),
                facePrimIdOffsets=Offsets,
                operationId=Operation,
                primary=False,
            ),
        )
    ]


def AddBodyMut(
    Author: AuthorState, Prefix: str, Count: int, Operations: tuple[int, ...]
) -> dict[str, object]:
    Reference = Author.Reference
    Author.Allocate("body_progenitor", "BodyProgenitor")
    Author.Allocate("body", "Body", ParentRole="bodies")
    Author.Allocate("bodies_root", "BodiesRoot", RootName="BodiesRoot")
    Author.Allocate("body_passive_ids", "PassiveIdGenerator")
    Author.Allocate("dc_body", "DcBody", ParentRole="fragment")
    Author.Change(
        "body_progenitor",
        bodyUuid=Author.BodyId,
        featureTagOccMap=[
            {"key": BodyTagInfo(Author, Count, Operation), "value": 1}
            for Operation in Operations
        ],
    )
    Author.Change(
        "body",
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles["body"]),
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=Author.BodyId,
        rGroupParent=Reference("bodies"),
        userName=Author.SpecValue.BodyName,
    )
    Author.Change("bodies_root", rootId="BodiesRoot", rooted=[Reference("body")])
    Author.Change(
        "bodies",
        creationIndex=1,
        groupChildren=[Reference("body")],
        passiveIdGenerator=Reference("body_passive_ids"),
    )
    Author.Change("body_passive_ids", rBodies=Reference("bodies"))
    Author.Change(
        "brep_history",
        mapBodyId=[{"key": Author.Policy.BodyKey, "value": Author.Roles["body"]}],
        partName=Author.BrepPart,
    )
    Author.Change(
        "dc_body",
        bodyUuid=Author.BodyId,
        rBody=Reference("body"),
        rOwnFeature=Reference(Prefix + "feature"),
    )
    Author.Change("fragment", dcBodies=[Reference("dc_body")])
    Author.Change(Prefix + "feature", dcBodies=[Reference("dc_body")])
    return {"first": Reference("body_progenitor"), "second": Count + 3}
