from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchGeom import (
    AddSketchGeom,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchNode import (
    AddSketchNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


def AddSketchRoot(
    Author: AuthorState, Prefix: str, Sketched: SketchPlan, NameValue: str, Ordinal: int
) -> None:
    Generation = Author.Policy.SketchGeneration
    RoleName = Prefix + "sketch"
    Author.Allocate(
        RoleName,
        "MSketch",
        ParentRole="sketches",
        NamedPairs=MakeAttributes(EntityGenesis=Generation),
    )
    if "sketches_root" not in Author.Roles:
        Author.Allocate("sketches_root", "SketchesRoot", RootName="SketchesRoot")
    Author.Allocate(Prefix + "ucs", "CoordinateSystem", ParentRole="component")
    Author.Allocate(
        Prefix + "origin",
        "Point3D",
        ParentRole=RoleName,
        Fields={
            "isFixed": True,
            "isFullyConstrained": True,
            "isOrigin": True,
            "isVisible": False,
        },
        NamedPairs=MakeAttributes(EntityGenesis=Generation, pt_tag=Sketched.OriginTag),
    )
    Author.Allocate(Prefix + "origin_uses", "CurveUses", ParentRole=Prefix + "origin")
    Author.Change(Prefix + "origin", curveUses=Author.Reference(Prefix + "origin_uses"))
    Author.Change(
        RoleName,
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles[RoleName]),
        UCS=Author.Reference(Prefix + "ucs"),
        rSketchGroupParent=Author.Reference("sketches"),
        userName=NameValue,
        creationIndex=Ordinal,
        isVisible=False,
    )


def AddSketchRecs(
    Author: AuthorState, Prefix: str, Sketched: SketchPlan, NameValue: str, Ordinal: int
) -> None:
    AddSketchRoot(Author, Prefix, Sketched, NameValue, Ordinal)
    AddSketchGeom(Author, Prefix, Sketched)
    AddSketchNode(Author, Prefix, Ordinal)
