from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFaces import CapFaces
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFaces import WallFaces
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def BuildShape(Solid: PrismSolid) -> ShapeBody:
    Faces: tuple[KShapeFace, ...] = (*WallFaces(Solid.Slabs), *CapFaces(Solid.Slabs))
    UseSenses: dict[KShapeEdge, list[bool]] = {}
    for FaceValue in Faces:
        for LoopValue in FaceValue.Loops:
            for UseValue in LoopValue:
                UseSenses.setdefault(UseValue.Edge, []).append(UseValue.Forward)
    for Senses in UseSenses.values():
        if sorted(Senses) != [False, True]:
            raise ValueError("Fusion part shape is not a closed two-manifold")
    return ShapeBody(Faces, Solid.BodyLabel, Solid.SketchCurves, Solid.Slabs[0].LowerCm)
