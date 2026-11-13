from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def AddPlaneCache(Author: AuthorState, Prefix: str) -> None:
    Reference = Author.Reference
    Author.Allocate(Prefix + "plane_recipe", "EntityRecipe")
    Author.Allocate(Prefix + "plane_cache", "ETCachedPlane")
    Author.Allocate(Prefix + "matrix_cache", "ETCachedMatrix3d")
    Author.Allocate(Prefix + "plane_seed", "EntityProgenitor")
    Author.Allocate(Prefix + "plane_seed_recipe", "EntityRecipe")
    PlaneId = Author.Roles["xy_plane"]
    Author.Change(Prefix + "plane_recipe", m_entityId=PlaneId)
    Author.Change(Prefix + "plane_seed_recipe", m_entityId=PlaneId)
    Author.Change(
        Prefix + "plane_seed", m_entityRecipe=Reference(Prefix + "plane_seed_recipe")
    )
    PlaneValue = dict(
        normalReversed=False,
        origin=MakePoint(),
        uAxis=MakePoint(1.0),
        vAxis=MakePoint(0.0, 1.0),
    )
    Author.Change(
        Prefix + "plane_cache",
        rCachedGeometry=PlaneValue,
        progenitor=Reference(Prefix + "plane_seed"),
    )


def AddSketchNode(Author: AuthorState, Prefix: str, Ordinal: int) -> None:
    Reference = Author.Reference
    MainRole = Prefix + "dc_sketch"
    AddNodeMut(Author, MainRole, "DcSketch", None)
    Author.Allocate(Prefix + "sketch_table", "ProgenitorTable")
    AddNodeMut(Author, Prefix + "plane", "EntityDataRef", MainRole)
    AddNodeMut(Author, Prefix + "matrix", "DRMatrix", MainRole)
    AddPlaneCache(Author, Prefix)
    Author.Change(
        MainRole,
        rSketch=Reference(Prefix + "sketch"),
        rSketchPlaneMatrix=Reference(Prefix + "matrix"),
        childNodes=[Reference(Prefix + "plane"), Reference(Prefix + "matrix")],
        featureBaseName="Sketch",
        featureIndex=Ordinal,
        rProgenitorTable=Reference(Prefix + "sketch_table"),
        isVisibleBeforeRollback=False,
    )
    Author.Change(
        Prefix + "plane",
        rRecipe=Reference(Prefix + "plane_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(Prefix + "plane_cache")],
        trackingType=33,
        updateFlag=4,
    )
    Author.Change(
        Prefix + "matrix",
        dataRefs=[Reference(Prefix + "plane")],
        caches=[Reference(Prefix + "matrix_cache")],
        trackingType=4,
    )
    Author.Change(Prefix + "sketch", rDcNode=Reference(MainRole))
