def PointMm(point):
    return [value * 10 for value in point.asArray()]


def EdgeGeometry(edge):
    import adsk.core

    if edge.geometry.objectType != adsk.core.Line3D.classType() or edge.startVertex is None or edge.endVertex is None or edge.isDegenerate:
        raise ValueError("only nondegenerate straight BRep edges have a complete native geometry comparison")
    return {"kind": "line", "start_mm": PointMm(edge.startVertex.geometry), "end_mm": PointMm(edge.endVertex.geometry)}


def MeasureBrep(body, gaps, label):
    import adsk.core

    vertices = [PointMm(vertex.geometry) for vertex in body.vertices]
    edges = []
    faces = []
    for index, edge in enumerate(body.edges):
        try:
            edges.append(EdgeGeometry(edge))
        except (RuntimeError, ValueError) as error:
            gaps.append(f"{label}:edge:{index}:{error}")
    for index, face in enumerate(body.faces):
        try:
            geometry = face.geometry
            if geometry.objectType != adsk.core.Plane.classType():
                raise ValueError("only planar BRep surfaces have a complete native geometry comparison")
            normal = list(geometry.normal.asArray())
            if face.isParamReversed:
                normal = [-value for value in normal]
            origin = PointMm(geometry.origin)
            loops = []
            for loop in face.loops:
                ring = []
                for coedge in loop.coEdges:
                    segment = EdgeGeometry(coedge.edge)
                    if coedge.isOpposedToEdge:
                        segment["start_mm"], segment["end_mm"] = segment["end_mm"], segment["start_mm"]
                    ring.append({key: segment[key] for key in ("start_mm", "end_mm")})
                loops.append(ring)
            faces.append({"kind": "plane", "normal": normal, "offset_mm": sum(a * b for a, b in zip(normal, origin)), "loops": loops})
        except (RuntimeError, ValueError) as error:
            gaps.append(f"{label}:face:{index}:{error}")
    return {"vertices_mm": vertices, "edges": edges, "faces": faces}
