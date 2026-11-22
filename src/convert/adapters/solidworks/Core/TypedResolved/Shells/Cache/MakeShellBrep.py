from dataclasses import replace as ReplaceValue

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# each rectangular prism supplies its oriented caps and wall trims from the same dimensions
def ShellPrism(BodyId: str, Minimum: SpaceVector, Maximum: SpaceVector) -> BrepModel:
    Corners = (
        PlaneVector(Minimum.x, Minimum.y),
        PlaneVector(Maximum.x, Minimum.y),
        PlaneVector(Maximum.x, Maximum.y),
        PlaneVector(Minimum.x, Maximum.y),
    )
    Profile = tuple(
        LineGeometry(Start, Finish)
        for Start, Finish in zip(Corners, (*Corners[1:], Corners[0]), strict=True)
    )
    return BuildPrism(BodyId, KTransformIdentity, Profile, Minimum.z, Maximum.z)[0]


# the reversed cavity cap loop belongs to the rim and the cavity walls face into the opening
def JoinShellRim(Outer: BrepModel, Inner: BrepModel) -> BrepModel:
    OuterTop, InnerTop = Outer.faces[1], Inner.faces[1]
    (LoopId,) = InnerTop.loop_ids
    (InnerLoop,) = tuple(Value for Value in Inner.loops if Value.id == LoopId)
    Opening = ReplaceValue(
        InnerLoop, coedge_ids=InnerLoop.coedge_ids[::-1], outer=False
    )
    RimFace = ReplaceValue(OuterTop, loop_ids=(*OuterTop.loop_ids, LoopId))
    FaceUses = Outer.face_uses + tuple(
        ReplaceValue(Value, reversed=True)
        for Value in Inner.face_uses
        if Value.face_id != InnerTop.id
    )
    (ShellValue,), (BodyValue,) = Outer.shells, Outer.bodies
    return ReplaceValue(
        Outer,
        curves=Outer.curves + Inner.curves,
        surfaces=Outer.surfaces
        + tuple(Value for Value in Inner.surfaces if Value.id != InnerTop.surface_id),
        vertices=Outer.vertices + Inner.vertices,
        edges=Outer.edges + Inner.edges,
        coedges=Outer.coedges
        + tuple(
            (
                ReplaceValue(Value, reversed=not Value.reversed)
                if Value.id in Opening.coedge_ids
                else Value
            )
            for Value in Inner.coedges
        ),
        loops=Outer.loops
        + tuple(Opening if Value is InnerLoop else Value for Value in Inner.loops),
        faces=tuple(RimFace if Value is OuterTop else Value for Value in Outer.faces)
        + tuple(Value for Value in Inner.faces if Value is not InnerTop),
        face_uses=FaceUses,
        shells=(
            ReplaceValue(ShellValue, face_use_ids=tuple(Value.id for Value in FaceUses)),
        ),
        bodies=(ReplaceValue(BodyValue, design_body_id=""),),
    )


# the cold solid follows the modeled stock bounds and one positive inward thickness
def MakeShellBrep(Footprint: ShellFootprint) -> BrepModel:
    Footprint.CheckInset()
    Minimum, Maximum = Footprint.Bounds.minimum, Footprint.Bounds.maximum
    Inset = Footprint.Thickness
    Outer = ShellPrism("shell-stock", Minimum, Maximum)
    Inner = ShellPrism(
        "shell-cavity",
        SpaceVector(Minimum.x + Inset, Minimum.y + Inset, Minimum.z + Inset),
        SpaceVector(Maximum.x - Inset, Maximum.y - Inset, Maximum.z),
    )
    BodyValue = JoinShellRim(Outer, Inner)
    if BodyValue.validate():
        raise ValueError(
            "fresh shell reconstruction does not form a valid closed solid"
        )
    return BodyValue
