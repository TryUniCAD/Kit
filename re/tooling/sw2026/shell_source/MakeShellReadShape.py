from dataclasses import replace

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector


def prism(name, left, bottom, right, top, low, high):
    corners = tuple(PlaneVector(x, y) for x, y in (
        (left, bottom), (right, bottom), (right, top), (left, top),
    ))
    contour = tuple(
        LineGeometry(a, b) for a, b in zip(corners, (*corners[1:], corners[0]), strict=True)
    )
    return BuildPrism(name, KTransformIdentity, contour, low, high)[0]


def build_shell(bounds, thickness, right):
    low, high = bounds.minimum, bounds.maximum
    outer = prism("outside", low.x, low.y, right, high.y, low.z, high.z)
    inner = prism(
        "cavity", low.x + thickness, low.y + thickness, right - thickness,
        high.y - thickness, low.z + thickness, high.z,
    )
    outer_top, inner_top = outer.faces[1], inner.faces[1]
    inner_open = inner_top.loop_ids[0]
    opening, = (loop for loop in inner.loops if loop.id == inner_open)
    rim = replace(outer_top, loop_ids=(*outer_top.loop_ids, inner_open))
    opening = replace(opening, coedge_ids=opening.coedge_ids[::-1], outer=False)
    faces = tuple(rim if row is outer_top else row for row in outer.faces) + tuple(
        row for row in inner.faces if row is not inner_top
    )
    uses = outer.face_uses + tuple(
        replace(row, reversed=True) for row in inner.face_uses if row.face_id != inner_top.id
    )
    loops = outer.loops + tuple(
        opening if row.id == inner_open else row for row in inner.loops
    )
    coedges = outer.coedges + tuple(
        replace(row, reversed=not row.reversed) if row.id in opening.coedge_ids else row
        for row in inner.coedges
    )
    return replace(
        outer, curves=(*outer.curves, *inner.curves),
        surfaces=(*outer.surfaces, *(row for row in inner.surfaces if row.id != inner_top.surface_id)),
        vertices=(*outer.vertices, *inner.vertices), edges=(*outer.edges, *inner.edges),
        coedges=coedges, loops=loops, faces=faces, face_uses=uses,
        shells=(replace(outer.shells[0], face_use_ids=tuple(row.id for row in uses)),),
        bodies=(replace(outer.bodies[0], design_body_id=None),),
    )
