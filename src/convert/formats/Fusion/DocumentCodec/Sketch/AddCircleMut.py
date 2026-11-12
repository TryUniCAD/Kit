from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def AddCircleMut(Author: AuthorState) -> None:
    Generation = Author.Policy.SketchGeneration
    FirstTag = Author.Policy.FirstSketchTag
    Author.Allocate(
        "circle_sketch",
        "MSketch",
        ParentRole="sketches",
        NamedPairs=MakeAttributes(EntityGenesis=Generation),
    )
    Author.Allocate("sketches_root", "SketchesRoot", RootName="SketchesRoot")
    Author.Allocate("sketch_coordinates", "CoordinateSystem", ParentRole="component")
    Author.Allocate(
        "sketch_origin",
        "Point3D",
        ParentRole="circle_sketch",
        Fields={
            "isFixed": True,
            "isFullyConstrained": True,
            "isOrigin": True,
            "isVisible": False,
        },
        NamedPairs=MakeAttributes(EntityGenesis=Generation, pt_tag=FirstTag),
    )
    Author.Allocate("origin_uses", "CurveUses", ParentRole="sketch_origin")
    Author.Allocate(
        "circle_center",
        "Point3D",
        ParentRole="circle_sketch",
        NamedPairs=MakeAttributes(EntityGenesis=Generation, pt_tag=FirstTag + 1),
    )
    Author.Allocate("center_uses", "CurveUses", ParentRole="circle_center")
    Author.Allocate(
        "circle",
        "CircArc3D",
        ParentRole="circle_sketch",
        NamedPairs=MakeAttributes(
            EntityGenesis=Generation, crv_primary_id=FirstTag + 2, crv_secondary_id=0
        ),
    )
    Author.Allocate("dc_sketch", "DcSketch", ParentRole="nodes")
    Author.Allocate("sketch_progenitors", "ProgenitorTable")
    Author.Allocate("sketch_plane", "EntityDataRef", ParentRole="nodes")
    Author.Allocate("plane_recipe", "EntityRecipe")
    Author.Allocate("sketch_matrix", "DRMatrix", ParentRole="nodes")
    Author.Allocate("plane_cache", "ETCachedPlane")
    Author.Allocate("matrix_cache", "ETCachedMatrix3d")
    Author.Allocate("plane_progenitor", "EntityProgenitor")
    Author.Allocate("plane_progenitor_recipe", "EntityRecipe")
    for RoleName in ("dc_sketch", "sketch_plane", "sketch_matrix"):
        Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
        Author.Allocate(RoleName + "_status", "DcStatus", NamedPairs=[])
