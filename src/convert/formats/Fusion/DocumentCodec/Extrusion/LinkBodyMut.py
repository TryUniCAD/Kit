from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Extrusion.MassCache import MassCache


def LinkBodyMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "body",
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles["body"]),
        cache=MassCache(Author),
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=Author.BodyId,
        physicalMaterial=Author.MakeValue("PhysicalMaterialValue"),
        rGroupParent=Reference("bodies"),
        userName=Author.SpecValue.BodyName,
        visualMaterial=Author.MakeValue("VisualMaterialValue"),
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
        rOwnFeature=Reference("dc_extrude"),
    )
    LabelBytes = Author.Policy.SideFaceLabel.encode("ascii")
    InfoValue = [
        Author.MakeGroup(
            "FeatureTagInfoValue",
            dict(
                facePrimIdData=list(LabelBytes),
                facePrimIdOffsets=[0, len(LabelBytes)],
                operationId=Author.Policy.FirstOperationId + 1,
                primary=False,
            ),
        )
    ]
    Author.Change(
        "body_progenitor",
        bodyUuid=Author.BodyId,
        featureTagOccMap=[
            {"key": InfoValue, "value": Author.Policy.BodyOccurrenceCount}
        ],
    )
    CurveTag, BodyTag = (
        Author.Policy.CurveProgenitorTag,
        Author.Policy.BodyProgenitorTag,
    )
    Author.Change(
        "extrude_progenitors",
        ProgenitorTagVec=[
            {"first": Reference("curve_progenitor"), "second": CurveTag},
            {"first": Reference("body_progenitor"), "second": BodyTag},
        ],
        tagId=max(CurveTag, BodyTag) + 1,
    )
