import math

from NativeAcceptance.NeutralSemantics import Vector


def NeutralBrep(document, gaps):
    from interchange.brep.Curves.BrepCurves import LineCurve
    from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
    from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass

    model = document.brep
    if model is None or len(document.bodies) != 1 or len(model.bodies) != 1:
        gaps.append("brep:single_body_partition")
        return None, None
    frame = model.bodies[0].transform
    if Vector(frame.origin) != [0, 0, 0] or Vector(frame.x_axis) != [1, 0, 0] or Vector(frame.y_axis) != [0, 1, 0] or Vector(frame.z_axis) != [0, 0, 1]:
        gaps.append("brep:body_transform")
        return None, None
    vertices = {item.id: Vector(item.point) for item in model.vertices}
    curves = {item.id: item for item in model.curves}
    edges = {}
    for item in model.edges:
        if not isinstance(curves.get(item.curve_id), LineCurve) or item.degenerate:
            gaps.append("brep:edge:" + item.id)
            continue
        edges[item.id] = {"kind": "line", "start_mm": vertices[item.start_vertex_id], "end_mm": vertices[item.end_vertex_id]}
    coedges = {item.id: item for item in model.coedges}
    loops = {item.id: item for item in model.loops}
    surfaces = {item.id: item for item in model.surfaces}
    faces = []
    for item in model.faces:
        surface = surfaces.get(item.surface_id)
        if not isinstance(surface, PlaneSurface):
            gaps.append("brep:face:" + item.id)
            continue
        normal = Vector(surface.normal)
        origin = Vector(surface.origin)
        face_loops = []
        for identity in item.loop_ids:
            boundary = []
            for key in loops[identity].coedge_ids:
                edge = edges.get(coedges[key].edge_id)
                if edge is None:
                    gaps.append("brep:loop:" + identity)
                    continue
                boundary.append({"start_mm": edge["start_mm"], "end_mm": edge["end_mm"]})
            face_loops.append(boundary)
        faces.append({"kind": "plane", "normal": normal, "offset_mm": sum(a * b for a, b in zip(normal, origin)), "loops": face_loops})
    counts = document.bodies[0].topology
    center = None
    if not gaps and counts.bounding_box is not None:
        mass = ReadPartMass(model, counts.bounding_box)
        if mass is not None and counts.volume is not None and math.isclose(mass.Volume, counts.volume, rel_tol=1e-9, abs_tol=1e-6):
            center = list(mass.Centroid)
    return {"vertices_mm": list(vertices.values()), "edges": list(edges.values()), "faces": faces}, center
