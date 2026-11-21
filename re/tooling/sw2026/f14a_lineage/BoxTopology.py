from itertools import product
from math import isclose, ulp


COUNTS = {"face": 6, "edge": 12, "vertex": 8}
SOURCE_KINDS = {b"Fa": "face", b"Ed": "edge", b"Ve": "vertex"}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def xyz(point):
    return point.x, point.y, point.z


def station(value, extent):
    if value == 0.0:
        return "0"
    require(isclose(value, extent, rel_tol=0.0, abs_tol=8 * ulp(extent)), "box station differs from its actual driver")
    return "1"


def corner(point, dimensions):
    return "".join(station(value, extent) for value, extent in zip(point, dimensions, strict=True))


def box_stations(points, dimensions):
    require(len(points) == 8 and {corner(point, dimensions) for point in points} == {"".join(row) for row in product("01", repeat=3)},
            "box has an ambiguous corner")


def axis_vector(actual, expected):
    return all(isclose(value, wanted, rel_tol=0.0, abs_tol=8 * ulp(1.0))
               for value, wanted in zip(actual, expected, strict=True))


def carrier_plane(origin, normal, corners, dimensions):
    tolerance = 8 * ulp(max(dimensions))
    return all(abs(sum((value - base) * n for value, base, n in zip(point, origin, normal, strict=True))) <= tolerance
               for point in corners)


def carrier_line(origin, direction, corners, dimensions, axis):
    tolerance = 8 * ulp(max(dimensions))
    for point in corners:
        parameter = (point[axis] - origin[axis]) / direction[axis]
        if any(abs(start + parameter * vector - value) > tolerance
               for start, vector, value in zip(origin, direction, point, strict=True)):
            return False
    return True


def incidence(corners):
    return "".join(axis[0] if len(set(axis)) == 1 else "*" for axis in zip(*corners, strict=True))


def enclosing_faces(role):
    return tuple("".join(flag if index == axis else "*" for index in range(3))
                 for axis, flag in enumerate(role) if flag != "*")


def add_role(roles, kind, role, owner_id, corners):
    require(role.count("*") == {"face": 2, "edge": 1, "vertex": 0}[kind]
            and role not in roles[kind], "duplicate or unqualified box entity role")
    require(set(corners) == {"".join(bits) for bits in product(*("01" if flag == "*" else flag for flag in role))},
            "entity boundary does not occupy its exact box role")
    roles[kind][role] = {"entity_id": owner_id, "corner_roles": sorted(corners), "touching_faces": sorted(enclosing_faces(role))}


def require_roles(roles):
    require({kind: len(values) for kind, values in roles.items()} == COUNTS, "incomplete box topology")
    return roles


def portable_roles(model, dimensions):
    from interchange.brep.Curves.BrepCurves import LineCurve
    from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface

    body, = model.bodies
    require(not model.validate(frozenset({body.design_body_id})) and len(model.shells) == len(model.regions) == 1
            and model.shells[0].closed and model.regions[0].solid, "strict model lacks one closed box solid")
    points = {vertex.id: xyz(vertex.point) for vertex in model.vertices}
    box_stations(tuple(points.values()), dimensions)
    corners = {owner_id: corner(point, dimensions) for owner_id, point in points.items()}
    corner_points = {role: points[key] for key, role in corners.items()}
    result = {kind: {} for kind in COUNTS}
    for owner_id, role in corners.items():
        add_role(result, "vertex", role, owner_id, (role,))
    edges, curves = {}, {curve.id: curve for curve in model.curves}
    for edge in model.edges:
        ends = [corners[owner_id] for owner_id in (edge.start_vertex_id, edge.end_vertex_id)]
        role = incidence(ends)
        add_role(result, "edge", role, edge.id, ends)
        axis = role.index("*")
        curve = curves[edge.curve_id]
        require(type(curve) is LineCurve and axis_vector(tuple(map(abs, xyz(curve.direction))), tuple(int(i == axis) for i in range(3)))
                and carrier_line(xyz(curve.origin), xyz(curve.direction), (corner_points[point] for point in ends), dimensions, axis),
                "box edge lacks its linked straight carrier")
        edges[edge.id] = role
    surfaces = {surface.id: surface for surface in model.surfaces}
    loops = {loop.id: loop for loop in model.loops}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    adjacency = {key: set() for key in edges}
    for face in model.faces:
        loop_id, = face.loop_ids
        edge_ids = tuple(coedges[coedge_id].edge_id for coedge_id in loops[loop_id].coedge_ids)
        require(len(set(edge_ids)) == 4 and loops[loop_id].outer, "box face does not own four distinct sides")
        used_corners = {end for edge_id in edge_ids for end in result["edge"][edges[edge_id]]["corner_roles"]}
        role = incidence(used_corners)
        add_role(result, "face", role, face.id, used_corners)
        axis, = (index for index, flag in enumerate(role) if flag != "*")
        carrier = surfaces[face.surface_id]
        require(type(carrier) is PlaneSurface and axis_vector(tuple(map(abs, xyz(carrier.normal))), tuple(int(i == axis) for i in range(3)))
                and station(xyz(carrier.origin)[axis], dimensions[axis]) == role[axis]
                and carrier_plane(xyz(carrier.origin), xyz(carrier.normal), (corner_points[point] for point in used_corners), dimensions),
                "box face carrier has another plane role")
        for edge_id in edge_ids:
            adjacency[edge_id].add(role)
    require(all(adjacency[edge_id] == set(enclosing_faces(role)) for edge_id, role in edges.items()),
            "typed edge incidence differs from its two actual face owners")
    return require_roles(result)


def located_shape(data, prefix, design_body):
    from convert.Geometry import Opencascade as occ

    reader = occ.Tokens(data)
    occ.ExpectHeader(reader)
    locations = occ.ModelLocations(reader)
    curves2, curves = occ.ReadModelCurves(reader, prefix)
    occ.ZeroTable(reader, b"Polygon3D")
    occ.ZeroTable(reader, b"PolygonOnTriangulations")
    surfaces = occ.ReadModelSurfs(reader, prefix)
    occ.ZeroTable(reader, b"Triangulations")
    count = occ.ReadCount(reader, b"TShapes", occ.KMaxShapes)
    records = occ.ShapeRecords(reader, count, len(curves), curves2, len(surfaces), len(locations))
    root = occ.ReadReference(reader, count, len(locations))
    require(count == 34 and root is not None and root.Orientation == "+" and records[root.RecordA].KindValue == b"So"
            and reader.PeekToken() is None and occ.HasLocations(records, root)
            and all(matrix == occ.KIdentityLocation for matrix in locations), "source is outside the measured located box topology")
    placement = occ.PlacementState(curves, surfaces, records, locations, prefix, [], [], {}, {}, {}, {})
    placed_root = occ.PlaceRecordMut(placement, root.RecordA, occ.KIdentityLocation)
    model = occ.BuildModel(tuple(placement.PlacedCurves), tuple(placement.PlacedSurfaces), placement.PlacedRecords,
                           occ.Reference(root.Orientation, placed_root), prefix, design_body, {})
    return records, root, placement.RecordCache, model


def indexed_occurrences(records, root):
    locations = {}
    orders = {kind: [] for kind in COUNTS}

    def visit(record, local_path):
        if record in locations:
            require(locations[record] == local_path, "one OCCT TShape has alternate occurrence locations")
            return
        locations[record] = local_path
        source = records[record]
        kind = SOURCE_KINDS.get(source.KindValue)
        if kind:
            orders[kind].append(record)
        for ref in source.Children:
            visit(ref.RecordA, local_path + ((ref.KLocation,) if ref.KLocation else ()))

    visit(root.RecordA, ())
    require(len(locations) == len(records) and {kind: len(order) for kind, order in orders.items()} == COUNTS,
            "first occurrence order has incomplete OCCT owners")
    return orders


def source_roles(data, prefix, design_body, dimensions):
    records, root, cache, model = located_shape(data, prefix, design_body)
    placements = {record: placed_index for (record, _), placed_index in cache.items()}
    require(len(placements) == len(cache) == len(records), "OCCT occurrence placement is ambiguous")
    roles = portable_roles(model, dimensions)
    orders = indexed_occurrences(records, root)
    result = {}
    for kind, order in orders.items():
        by_id = {row["entity_id"]: role for role, row in roles[kind].items()}
        result[kind] = {by_id[f"{prefix}:{kind}:{placements[record]}"]:
                        {"indexed_name": kind.title() + str(index), "ordinal": index,
                         "tshape_reference": record, "neutral_entity_id": f"{prefix}:{kind}:{placements[record]}"}
                        for index, record in enumerate(order, 1)}
    return result
