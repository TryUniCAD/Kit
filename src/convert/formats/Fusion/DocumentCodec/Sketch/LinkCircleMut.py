from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint
from math import pi as KPiValue


def LinkCircleMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "circle_sketch",
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles["circle_sketch"]),
        rDcNode=Reference("dc_sketch"),
        UCS=Reference("sketch_coordinates"),
        rSketchGroupParent=Reference("sketches"),
        userName=Author.SpecValue.SketchName,
    )
    Author.Change(
        "sketches_root", rootId="SketchesRoot", rooted=[Reference("circle_sketch")]
    )
    Author.Change("sketch_origin", curveUses=Reference("origin_uses"))
    Author.Change("circle_center", curveUses=Reference("center_uses"))
    Author.Change("center_uses", geometries=[Reference("circle")])
    ArcFields = dict(
        center=MakePoint(),
        normal=MakePoint(0.0, 0.0, 1.0),
        refVec=MakePoint(1.0),
        radius=Author.SpecValue.RadiusMm / 10.0,
        startAngle=0.0,
        endAngle=2.0 * KPiValue,
    )
    Author.Change("circle", arcCurve=ArcFields, rCenterPoint=Reference("circle_center"))
    Author.Change(
        "dc_sketch",
        rSketch=Reference("circle_sketch"),
        rSketchPlaneMatrix=Reference("sketch_matrix"),
        childNodes=[Reference("sketch_plane"), Reference("sketch_matrix")],
        featureBaseName="Sketch",
        rProgenitorTable=Reference("sketch_progenitors"),
    )
    ScopeValue = [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=Author.ComponentId,
                scopeIdType=2,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
    Author.Change(
        "sketch_plane",
        rRecipe=Reference("plane_recipe"),
        rScope=ScopeValue,
        caches=[Reference("plane_cache")],
        trackingType=33,
        updateFlag=4,
        rParentFeature=Reference("dc_sketch"),
    )
    Author.Change("plane_recipe", m_entityId=Author.Roles["xy_plane"])
    Author.Change(
        "sketch_matrix",
        dataRefs=[Reference("sketch_plane")],
        caches=[Reference("matrix_cache")],
        trackingType=4,
        rParentFeature=Reference("dc_sketch"),
    )
    PlaneValue = dict(
        normalReversed=False,
        origin=MakePoint(),
        uAxis=MakePoint(1.0),
        vAxis=MakePoint(0.0, 1.0),
    )
    Author.Change(
        "plane_cache",
        rCachedGeometry=PlaneValue,
        progenitor=Reference("plane_progenitor"),
    )
    Author.Change(
        "plane_progenitor", m_entityRecipe=Reference("plane_progenitor_recipe")
    )
    Author.Change("plane_progenitor_recipe", m_entityId=Author.Roles["xy_plane"])
    for RoleName in ("dc_sketch", "sketch_plane", "sketch_matrix"):
        Author.Change(
            RoleName,
            status=Reference(RoleName + "_status"),
            rDynamicUpdateData=Reference(RoleName + "_dynamic"),
        )
        Author.Change(
            RoleName + "_dynamic",
            rOwnerNode=Reference(RoleName),
            timeStamp=Author.Policy.TimeStamp,
        )
    Author.Change(
        "sketches", highWaterMark=1, groupChildren=[Reference("circle_sketch")]
    )
    Author.FindEntity("sketches").NamedPairs = MakeAttributes(
        crv_tag_id_idx=Author.Policy.FirstSketchTag + 3
    )
    Author.Change("fragment", featureIndexMap=[{"key": "DcSketchMetaType", "value": 1}])
    Author.Change("creation_order", representationFeatures=[Reference("dc_sketch")])
    Author.Change(
        "feature_ids",
        featureIdMap=[
            {"key": Author.Policy.FirstOperationId, "value": Author.Roles["dc_sketch"]}
        ],
    )
    Author.Change("component", operationSeedId=Author.Policy.FirstOperationId + 1)
