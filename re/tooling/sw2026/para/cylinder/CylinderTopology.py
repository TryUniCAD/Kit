from dataclasses import dataclass
from math import dist

from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import CircleGraph
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import CirclePlan
from para.rectangle.Allocate import DraftNode, Ref, require, world
from para.rectangle.Geometry import FaceRole, chain


@dataclass(frozen=True)
class CylinderTopology:
    body: Ref
    side: Ref
    start: Ref
    end: Ref
    nodes: tuple[DraftNode, ...]

    def face_roles(self, arc_marker):
        return (
            (self.side, FaceRole(False, arc_marker)),
            (self.start, FaceRole(True, 1)),
            (self.end, FaceRole(True, 0)),
        )


def translate(point, axis, distance):
    return tuple(p + direction * distance for p, direction in zip(point, axis, strict=True))


def cap_topology(cap, side_loop, body, point, axis, radial, radius, sense):
    loop = Ref(f"{cap.name}:loop")
    cap_fin = Ref(f"{loop.name}:fin")
    side_fin = Ref(f"{side_loop.name}:fin")
    edge = Ref(f"{cap.name}:edge")
    curve = Ref(f"{cap.name}:circle")
    surface = Ref(f"{cap.name}:plane")
    nodes = (
        DraftNode(loop, 15, {"face": cap, "halfedge": cap_fin, "next": 0}),
        DraftNode(edge, 16, {
            "owner": body, "curve": curve, "halfedge": cap_fin if sense == "+" else side_fin,
            "next_on_curve": 0, "previous_on_curve": 0,
        }),
        DraftNode(curve, 31, {
            "owner": edge, "sense": "+", "centre": point, "normal": axis, "x_axis": radial, "radius": radius,
        }),
        DraftNode(surface, 50, {"owner": cap, "sense": "+", "pvec": point, "normal": axis, "x_axis": radial}),
    )
    fins = (
        (cap_fin, side_fin, loop, sense),
        (side_fin, cap_fin, side_loop, "+" if sense == "-" else "-"),
    )
    return nodes + tuple(
        DraftNode(fin, 17, {
            "loop": owner, "edge": edge, "other": other, "forward": fin, "backward": fin,
            "vertex": 0, "sense": orientation, "curve": 0,
        })
        for fin, other, owner, orientation in fins
    )


def generated_cylinder(candidate, marks):
    plan = candidate.PlanValue
    profile = candidate.ProfileValue
    circle = profile.GeometryValue
    require(type(plan) is CirclePlan and type(circle) is CircleGraph and plan.AxisValue == "z"
            and plan.PlaneName == "Front Plane" and plan.IsDiameter
            and plan.EndValue.ModeValue == "blind" and plan.SecondDepth is None
            and not plan.EndValue.IsReversed and candidate.BossValue.ProfileValue is profile,
            "cylinder cache experiment requires a generated forward blind Front diameter circle")
    require(profile.ProfileValue.FieldsValue["pd_f80"] is circle.SketchValue
            and circle.SketchValue.FieldsValue["arcs"][0]["arc"] is circle.ArcValue.FieldsValue
            and circle.ArcValue.FieldsValue["_center"] is circle.CenterValue
            and circle.ArcValue.FieldsValue["_start"] is circle.ArcValue.FieldsValue["_end"] is circle.MarkerValue,
            "the closed circle must retain its actual sketch, centre and endpoint owners")

    frame = profile.FrameValue
    centre = circle.CenterValue.FieldsValue["pos"]
    marker = circle.MarkerValue.FieldsValue["pos"]
    radius = plan.CircleValue.RadiusValue
    require((centre["x"], centre["y"]) == plan.CircleValue.CenterValue
            and dist((centre["x"], centre["y"]), (marker["x"], marker["y"])) > 0
            and (marker["x"], marker["y"]) == plan.CircleValue.MarkerValue,
            "circle plan and constructed sketch geometry differ")
    axis, radial = frame.NormalValue, frame.AxisU
    start_point = translate(translate(frame.OriginValue, radial, centre["x"]), frame.AxisV, centre["y"])
    end_point = translate(start_point, axis, plan.DepthValue)
    require(end_point != start_point, "cylinder extent must be representable")

    body = Ref(plan.BodyId)
    interior, exterior, solid_shell, void_shell = (
        Ref(f"{body.name}:{role}") for role in ("solid", "void", "solid-shell", "void-shell")
    )
    side, start, end = (Ref(f"{body.name}:{role}") for role in ("side", "start", "end"))
    axial_surface = Ref(f"{side.name}:cylinder")
    side_loops = tuple(Ref(f"{side.name}:loop:{role}") for role in ("start", "end"))
    faces = (side, start, end)
    neighbors = chain(face.name for face in faces)
    nodes = [
        world(marks, body),
        DraftNode(body, 12, {
            "owner": Ref("world"), "shell": solid_shell, "region": exterior, "edge": Ref(f"{start.name}:edge"),
            "vertex": 0, "boundary_point": 0, "boundary_curve": Ref(f"{start.name}:circle"),
            "boundary_surface": axial_surface,
        }),
        DraftNode(exterior, 19, {"body": body, "next": interior, "previous": 0, "shell": void_shell, "type": "V"}),
        DraftNode(interior, 19, {"body": body, "next": 0, "previous": exterior, "shell": solid_shell, "type": "S"}),
        DraftNode(solid_shell, 13, {"body": body, "region": interior, "face": side, "front_face": 0}),
        DraftNode(void_shell, 13, {"body": 0, "region": exterior, "face": 0, "front_face": side}),
    ]
    surfaces = (axial_surface, Ref(f"{start.name}:plane"), Ref(f"{end.name}:plane"))
    first_loops = (side_loops[0], Ref(f"{start.name}:loop"), Ref(f"{end.name}:loop"))
    for face, surface, loop, sense in zip(faces, surfaces, first_loops, ("+", "-", "+"), strict=True):
        previous, following = neighbors[face.name]
        nodes.append(DraftNode(face, 14, {
            "shell": solid_shell, "front_shell": void_shell, "loop": loop, "surface": surface,
            "previous": previous, "next": following, "previous_front": previous, "next_front": following,
            "next_on_surface": 0, "previous_on_surface": 0, "sense": sense,
        }))
    for name, following in zip(side_loops, (side_loops[1], 0), strict=True):
        nodes.append(DraftNode(name, 15, {
            "face": side, "halfedge": Ref(f"{name.name}:fin"), "next": following,
        }))
    nodes.append(DraftNode(axial_surface, 51, {
        "owner": side, "sense": "+", "pvec": start_point, "axis": axis,
        "radius": radius, "x_axis": radial,
    }))
    for cap, side_loop, point, sense in zip((start, end), side_loops, (start_point, end_point), ("-", "+"), strict=True):
        nodes.extend(cap_topology(cap, side_loop, body, point, axis, radial, radius, sense))
    return CylinderTopology(body, side, start, end, tuple(nodes))
