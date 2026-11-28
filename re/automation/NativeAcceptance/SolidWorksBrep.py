import math

from NativeAcceptance.SolidWorksCom import Member


def ReadPoint(vertex):
    if vertex is None:
        raise ValueError("closed or unbounded native edge has no distinct vertices")
    point = list(Member(vertex, "GetPoint"))
    if len(point) != 3 or not all(math.isfinite(value) for value in point):
        raise ValueError("native vertex is not a finite spatial point")
    return [float(value) * 1000 for value in point]


def ReadEdge(edge):
    curve = Member(edge, "GetCurve")
    if curve is None or not Member(curve, "IsLine"):
        raise ValueError("native body edge is not a straight line")
    return {"kind": "line", "start_mm": ReadPoint(Member(edge, "GetStartVertex")), "end_mm": ReadPoint(Member(edge, "GetEndVertex"))}


def MeasureBrep(body, label, gaps):
    try:
        vertices = Member(body, "GetVertices") or ()
        edges = Member(body, "GetEdges") or ()
        faces = Member(body, "GetFaces") or ()
        if max(len(vertices), len(edges), len(faces)) > 16384:
            raise ValueError("native body topology exceeds the measurement limit")
        result = {"vertices_mm": [ReadPoint(vertex) for vertex in vertices], "edges": [ReadEdge(edge) for edge in edges], "faces": []}
        for face in faces:
            surface = Member(face, "GetSurface")
            if surface is None or not Member(surface, "IsPlane"):
                raise ValueError("native body face is not planar")
            values = list(surface.PlaneParams)
            if len(values) != 6 or not all(math.isfinite(value) for value in values):
                raise ValueError("native plane parameters are unavailable")
            normal = [float(value) for value in values[:3]]
            if not math.isclose(math.hypot(*normal), 1, abs_tol=1e-9):
                raise ValueError("native plane normal is not a unit vector")
            loops = []
            for loop in Member(face, "GetLoops") or ():
                loop_edges = Member(loop, "GetEdges") or ()
                if len(loop_edges) < 3 or len(loop_edges) > 16384:
                    raise ValueError("native planar loop has unsupported edge cardinality")
                loops.append([{key: value for key, value in ReadEdge(edge).items() if key != "kind"} for edge in loop_edges])
            if not loops:
                raise ValueError("native planar face has no bounded loops")
            result["faces"].append({"kind": "plane", "normal": normal, "offset_mm": sum(a * b for a, b in zip(normal, values[3:])) * 1000, "loops": loops})
        if not vertices or not edges or not faces:
            raise ValueError("native solid has incomplete topology")
        return result
    except Exception as error:
        gaps.append(f"{label}:brep:{type(error).__name__}:{str(error)[:160]}")
        return None
