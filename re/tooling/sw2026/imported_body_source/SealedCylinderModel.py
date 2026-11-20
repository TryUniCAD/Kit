from math import hypot, isclose, isfinite, tau

from SealedCylinderPacket import require
from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


def coordinates(value):
    return (value.x, value.y, value.z)


def negate(value):
    return SpaceVector(*(-component for component in coordinates(value)))


def canonical_radial(axis):
    index = min(range(3), key=lambda i: (abs(axis[i]), i))
    projection = tuple(float(i == index) - axis[index] * a for i, a in enumerate(axis))
    length = hypot(*projection)
    return SpaceVector(*(component / length for component in projection))


def validated_specification(specification):
    require(
        type(specification) is dict
        and set(specification) == {"face_center_m", "axis", "radius_m", "height_m"},
        "private cylinder recipe has additional domains",
    )
    for name in ("face_center_m", "axis"):
        values = specification[name]
        require(
            type(values) is list
            and len(values) == 3
            and all(type(value) is float and isfinite(value) for value in values),
            "private author recipe requires finite SI triples",
        )
    for name in ("radius_m", "height_m"):
        value = specification[name]
        require(
            type(value) is float and isfinite(value) and value > 0.0,
            "private cylinder dimensions must be finite and positive",
        )
    require(
        isclose(hypot(*specification["axis"]), 1.0, rel_tol=0.0, abs_tol=1e-12),
        "private signed axis is not unit length",
    )
    return specification


def ordered_boundary(specification):
    spec = validated_specification(specification)
    axis = SpaceVector(*spec["axis"])
    radial = canonical_radial(spec["axis"])
    start = SpaceVector(*(value * 1000.0 for value in spec["face_center_m"]))
    radius = spec["radius_m"] * 1000.0
    far = OffsetVector(start, axis, spec["height_m"] * 1000.0)
    side = CylinderSurface("mantle-surface", start, axis, radial, radius)
    faces, surfaces, loops, coedges, edges, curves, vertices = (
        [],
        [side],
        [],
        [],
        [],
        [],
        [],
    )
    for name, point, normal, reference in (
        ("far", far, axis, radial),
        ("near", start, negate(axis), negate(radial)),
    ):
        rim = CircleCurve(
            name + "-circle", point, negate(normal), negate(reference), radius
        )
        cap = PlaneSurface(name + "-plane", point, normal, reference)
        seam = BrepVertex(
            name + "-seam", OffsetVector(rim.center, rim.reference_direction, radius)
        )
        edge = BrepEdge(name + "-edge", seam.id, seam.id, rim.id, 0.0, tau)
        cap_use = BrepCoedge(name + "-cap-use", edge.id, reversed=True)
        side_use = BrepCoedge(name + "-side-use", edge.id)
        cap_loop = BrepLoop(name + "-cap-loop", (cap_use.id,), outer=True)
        side_loop = BrepLoop(name + "-side-loop", (side_use.id,), outer=name == "far")
        faces.append(BrepFace(name + "-cap", cap.id, (cap_loop.id,)))
        surfaces.append(cap)
        loops.extend((cap_loop, side_loop))
        coedges.extend((cap_use, side_use))
        edges.append(edge)
        curves.append(rim)
        vertices.append(seam)
    faces.append(BrepFace("mantle", side.id, ("far-side-loop", "near-side-loop")))
    uses = tuple(BrepFaceUse(face.id + "-use", face.id) for face in faces)
    shell = BrepShell("shell", tuple(use.id for use in uses), closed=True)
    shell_use = BrepShellUse("shell-use", shell.id)
    region = BrepRegion("region", (shell_use.id,), solid=True)
    return BrepModel(
        curves=tuple(curves),
        surfaces=tuple(surfaces),
        vertices=tuple(vertices),
        edges=tuple(edges),
        coedges=tuple(coedges),
        loops=tuple(loops),
        faces=tuple(faces),
        face_uses=uses,
        shells=(shell,),
        shell_uses=(shell_use,),
        regions=(region,),
        bodies=(BrepBody("solid", (region.id,)),),
    )


def geometry_document(specification):
    return CadDocument(
        CadSource("kit.neutral", "", ""),
        (Configuration("selected", "Default", True),),
        (),
        (),
        (),
        (),
        (),
        (),
        brep=ordered_boundary(specification),
        capabilities=frozenset({Capability.KBrep, Capability.KConfigurations}),
    )
