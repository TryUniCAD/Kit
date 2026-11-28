from hashlib import sha256

from BoxTopology import COUNTS, add_role, axis_vector, box_stations, carrier_line, carrier_plane, corner, incidence, require, require_roles, station


def part_owners(part, document, dimensions):
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Features.FeatureExtrude import ExtrudeEnd
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Transform import KTransformIdentity

    link = ReadNativeLink(part, 0)
    model = link.ConfigValue.RootValue
    features = {NativeNodeId(node): node for node in link.ResolvedValue.RootsValue if node is not None}
    boss, = (node for node in features.values() if node.ClassValue.NameValue == "moExtrusion_c")
    feature_id = NativeNodeId(boss)
    extrude = ReadExtrude(link, boss, features)
    profile_id = NativeNodeId(extrude.ProfileValue)
    require(extrude.ModeValue == ExtrudeEnd.KBlind and not extrude.IsReversed and extrude.SecondValue is None,
            "part does not have the qualified forward single boss")
    sketch, = document.sketches
    plane, = (node for node in document.support_planes if sketch.support_plane_id == node.id)
    parameters = {item.name: item.value.value for item in document.parameters}
    require(plane.name == "Front Plane" and plane.transform == KTransformIdentity
            and sketch.id == f"sldprt:sketch:{profile_id}" and parameters == dict(zip(("Length", "Width", "Height"), dimensions, strict=True)),
            "actual typed frame, profile or active drive changed")
    body, = document.bodies
    require(body.final_feature_id == f"sldprt:feature:{feature_id}" and document.brep.bodies[0].design_body_id == body.id,
            "strict body does not bind to the actual extrusion owner")
    attached, = (row["o"] for row in boss.FieldsValue["f528"]["items"])
    managed, = (row["o"] for row in model.FieldsValue["fd88"]["atoms"])
    atom = managed.FieldsValue
    require(managed is attached and managed.ClassValue.NameValue == "moAtom_c"
            and atom["f12c"] == atom["f130"] == feature_id and boss.FieldsValue["f498"] == [{"v": atom["f140"]}],
            "resolved feature and configuration disagree about the actual active atom")
    lines = tuple(value for value in sketch.entities if type(value.geometry) is LineGeometry and not value.construction)
    sketch_points = {(point.x, point.y) for line in lines for point in (line.geometry.start, line.geometry.end)}
    box_stations(tuple((x, y, z) for x, y in sketch_points for z in (0.0, dimensions[2])), dimensions)
    markers = {}
    for line in lines:
        native_marker = line.attributes["native_line_permanent_id"]
        ends = tuple((entry.x, entry.y, 0.0) for entry in (line.geometry.start, line.geometry.end))
        role = incidence(tuple(corner(point, dimensions)[:2] + "*" for point in ends))
        require(role not in markers and role.count("*") == 2 and type(native_marker) is int and native_marker > 0,
                "sketch line does not uniquely produce a side boundary")
        markers[role] = {"permanent_marker": native_marker, "creation_marker": line.attributes["native_line_creation_id"],
                         "sketch_entity_id": line.id}
    require(len(markers) == len({row["permanent_marker"] for row in markers.values()}) == 4,
            "side roles lack four distinct actual sketch lines")
    config_header = link.ConfigValue.HeaderValue
    document_header = ReadHeaderGraph(part.require("Header2"), link.ConfigValue.VersionValue)
    time = DatumTime(config_header, feature_id)
    require(time == DatumTime(document_header, feature_id), "headers disagree on the feature-reference time")
    has_boss_log = any(log.FieldsValue["f48"] == feature_id and ReadLogItems(log, "moStamp_c")
                       for log in ReadLogItems(config_header.FieldsValue["f20"], "moLogs_c"))
    mark = lambda row: None if row is None else row.FieldsValue["f18"]
    return {"boss_id": feature_id, "profile_id": profile_id, "body_atom_id": atom["f140"],
            "archive_body_tags": [atom["f180"], atom["f1b0"]], "has_producer_creation_event": bool(has_boss_log),
            "feature_reference_time": time, "side_markers": markers,
            "configuration_mark": mark(model.FieldsValue.get("fe38")), "boss_mark": mark(boss.FieldsValue.get("f3d0"))}


def attribute_words(nodes, attribute, lane):
    from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt

    return RequireXmt(nodes, attribute.Indexes("fields")[lane], 82).Indexes("values")


def owned_wire_boundary(nodes, body, dimensions):
    from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
    from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
    from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain

    members = lambda kind: {index for index, node in nodes.items() if node.KindValue == kind}
    vertex_ids = WalkXmtChain(nodes, body.Integer("vertex"), 18, OwnerField="owner", OwnerValue=body.IndexValue)
    edge_ids = WalkXmtChain(nodes, body.Integer("edge"), 16, OwnerField="owner", OwnerValue=body.IndexValue)
    shell = RequireXmt(nodes, body.Integer("shell"), 13)
    require(shell.Integer("body") == body.IndexValue, "kernel shell has a foreign solid owner")
    face_ids = WalkXmtChain(nodes, shell.Integer("face"), 14, OwnerField="shell", OwnerValue=shell.IndexValue)
    require(set(vertex_ids) == members(18) and set(edge_ids) == members(16) and set(face_ids) == members(14),
            "solid boundary omits an active record")
    points = {}
    for index in vertex_ids:
        carrier = RequireXmt(nodes, nodes[index].Integer("point"), 29)
        require(carrier.Integer("owner") == index, "kernel vertex does not own its point")
        points[index] = tuple(value * 1000.0 for value in ReadXmtVector(carrier, "pvec"))
    box_stations(tuple(points.values()), dimensions)
    corners = {index: corner(point, dimensions) for index, point in points.items()}
    corner_points = {role: points[index] for index, role in corners.items()}
    result = {kind: {} for kind in COUNTS}
    for index, role in corners.items():
        add_role(result, "vertex", role, index, (role,))
    edge_roles = {}
    for index in edge_ids:
        node = nodes[index]
        fin = RequireXmt(nodes, node.Integer("halfedge"), 17)
        other = RequireXmt(nodes, fin.Integer("other"), 17)
        require(fin.Integer("edge") == index == other.Integer("edge") and other.Integer("other") == fin.IndexValue
                and {fin.String("sense"), other.String("sense")} == {"-", "+"}, "kernel edge lacks opposite live fins")
        endpoints = tuple(corners[value.Integer("vertex")] for value in (fin, other))
        role = incidence(endpoints)
        add_role(result, "edge", role, index, endpoints)
        edge_roles[index] = role
        carrier = RequireXmt(nodes, node.Integer("curve"), 30)
        varying = role.index("*")
        direction = ReadXmtVector(carrier, "direction")
        origin = tuple(value * 1000.0 for value in ReadXmtVector(carrier, "pvec"))
        require(carrier.Integer("owner") == index
                and axis_vector(tuple(map(abs, direction)), tuple(int(i == varying) for i in range(3)))
                and carrier_line(origin, direction, (corner_points[point] for point in endpoints), dimensions, varying),
                "kernel edge curve does not occupy its linked endpoints")
    fins_seen, adjacency = set(), {edge: set() for edge in edge_ids}
    for index in face_ids:
        face = nodes[index]
        loop = RequireXmt(nodes, face.Integer("loop"), 15)
        require(loop.Integer("face") == index and loop.Integer("next") == 0, "kernel face has a foreign or extra loop")
        seed = fin_index = loop.Integer("halfedge")
        ends = []
        loop_edges = []
        for _ in range(4):
            fin = RequireXmt(nodes, fin_index, 17)
            require(fin_index not in fins_seen and fin.Integer("loop") == loop.IndexValue, "kernel fin does not own its active loop role")
            fins_seen.add(fin_index)
            next_fin = RequireXmt(nodes, fin.Integer("forward"), 17)
            opposite_next = RequireXmt(nodes, next_fin.Integer("other"), 17)
            require(next_fin.Integer("backward") == fin_index and opposite_next.Integer("vertex") == fin.Integer("vertex"),
                    "kernel loop does not close through actual directed vertices")
            loop_edges.append(fin.Integer("edge"))
            ends.append(corners[fin.Integer("vertex")])
            fin_index = next_fin.IndexValue
        require(fin_index == seed and len(set(loop_edges)) == 4, "kernel face has another active boundary shape")
        role = incidence(ends)
        add_role(result, "face", role, index, ends)
        axis, = (i for i, flag in enumerate(role) if flag != "*")
        plane = RequireXmt(nodes, face.Integer("surface"), 50)
        expected_normal = tuple((2 * int(role[axis]) - 1) if i == axis else 0 for i in range(3))
        sign = {"+": 1, "-": -1}[face.String("sense")]
        normal = tuple(sign * value for value in ReadXmtVector(plane, "normal"))
        origin = tuple(value * 1000.0 for value in ReadXmtVector(plane, "pvec"))
        require(plane.Integer("owner") == index and axis_vector(normal, expected_normal)
                and station(origin[axis], dimensions[axis]) == role[axis]
                and carrier_plane(origin, normal, (corner_points[point] for point in ends), dimensions),
                "kernel face carrier does not have the actual outward plane role")
        for edge in loop_edges:
            adjacency[edge].add(role)
    require(fins_seen == members(17) and all(adjacency[edge] == set(result["edge"][role]["touching_faces"])
                                           for edge, role in edge_roles.items()), "kernel fins disagree with actual adjacent faces")
    return require_roles(result), [sorted(set(axis)) for axis in zip(*points.values(), strict=True)]


def expected_primary(role, owners):
    creator = (owners["boss_id"], owners["feature_reference_time"], 0)
    if role in owners["side_markers"]:
        return (74, *creator, owners["side_markers"][role]["permanent_marker"])
    require(role in {"**0", "**1"}, "box face has no actual cap or side role")
    return (40, *creator, int(role[2]), 0)


def compare_saved_nodes(nodes, roles, public, owners):
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs

    matched = {kind: {} for kind in COUNTS}
    for kind in COUNTS:
        require(roles[kind].keys() == public[kind].keys(), "public and physical kernel entity roles differ")
        for role, row in roles[kind].items():
            node = nodes[row["entity_id"]]
            view = public[kind][role]
            require(row["corner_roles"] == view["corner_roles"] and row["touching_faces"] == view["touching_faces"],
                    "public and physical kernel boundary incidence differs")
            attrs = ReadBodyAttrs(nodes, node)
            record = {"sdk_entity_id": view["entity_id"], "kernel_node_id": node.Integer("node_id"),
                      "normalized_transmit_index": node.IndexValue, "wire_transmit_index": node.IndexValue + 1,
                      "attribute_names": sorted(attrs), "incident_face_roles": row["touching_faces"]}
            if kind == "face":
                lanes = attrs["FACE_ID_2001"].Indexes("fields")
                require(len(lanes) == 4 and lanes[:2] == (0, 0), "native planar face has alternate identity lanes")
                primary = attribute_words(nodes, attrs["FACE_ID_2001"], 2)
                require(primary == expected_primary(role, owners), "serialized face identity differs from its geometric producer")
                record.update(primary_face_identity=primary, auxiliary_face_identity=attribute_words(nodes, attrs["FACE_ID_2001"], 3),
                              unchanged_stamp=attribute_words(nodes, attrs["SWEntUnchanged"], 0),
                              downstream_face_identity=attribute_words(nodes, attrs["DOWNSTREAM_FACE_ID"], 0))
            else:
                require(not attrs, "saved edge or vertex has an unqualified identity attribute")
            matched[kind][role] = record
        require(len({row["kernel_node_id"] for row in matched[kind].values()}) == COUNTS[kind], "local kernel node identifiers are ambiguous")
    return matched


def compare_node(typed, research):
    fields = research.fields
    if research.kind == 84:
        fields = fields | {"values": fields["values"].encode("ascii")}
    return typed.KindValue == research.kind and typed.FieldsValue == fields


def saved_kernel(part, document, portable, owners, cold_owners, dimensions):
    from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
    from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
    from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
    from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
    from convert.adapters.solidworks.Container.Format import KPartitionStream
    from convert.adapters.solidworks.Container.Parasolid import DecodePartition
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
    from para.Partition import frame_payloads, read_partition, write_payloads

    stream = part.require(KPartitionStream)
    active, history = DecodePartition(stream, KPartitionStream)
    attached, = (row for row in document.brep_payloads if row.source_stream == KPartitionStream and row.kind == "partition")
    require(active.data == attached.data and active.sha256 == attached.sha256 and history.kind == "deltas",
            "strict part does not bind the actual selected native partition")
    nodes = ReadActiveNodes(active.data)
    CheckXmtGraph(nodes)
    ReadXmtHistory(history.data, nodes)
    partition = read_partition(stream)
    require(frame_payloads(write_payloads(partition)) == stream and len(partition.nodes) == len(nodes)
            and all(compare_node(nodes[row.index], row) for row in partition.nodes),
            "complete selected active and rollback wire grammar differs")
    body = RequireXmt(nodes, RequireXmt(nodes, 1, 101).Integer("body"), 12)
    attrs = ReadBodyAttrs(nodes, body)
    atom_id, = attribute_words(nodes, attrs["ATOM_ID_2001"], 1)
    feature_id, = attribute_words(nodes, attrs["LAST_BODY_MODIFYING_FEATURE_ID"], 1)
    tag, = attribute_words(nodes, attrs["BODY_MATCH"], 0)
    require(atom_id == owners["body_atom_id"] == cold_owners["body_atom_id"]
            and feature_id == owners["boss_id"] == cold_owners["boss_id"]
            and owners["archive_body_tags"] == [tag, tag] and cold_owners["archive_body_tags"] == [0, 0],
            "the measured saved kernel body does not resolve to the same actual producer and atom")
    marks = {row.mark.index: row for row in partition.history}
    selected = marks[partition.root.fields["current_pmark"]]
    active_mark = selected.mark.fields["id"]
    prior_mark = marks[selected.mark.fields["preceding"]].mark.fields["id"]
    require(owners["boss_mark"] == active_mark and owners["configuration_mark"] == prior_mark
            and {row.mark.fields["id"] for row in marks.values()} == {1, prior_mark, active_mark},
            "configuration and producer marks differ from the retained history")
    require(all(row.rollback is None or row.rollback.previous_world.fields["body"] == 0 for row in marks.values())
            and (body.IndexValue, body.KindValue) in selected.rollback.deleted,
            "rollback has a different topology history")
    raw_roles, actual_stations = owned_wire_boundary(nodes, body, dimensions)
    carriers = (node.FieldsValue[field] for node in nodes.values() for kind, field in ((30, "direction"), (50, "normal"))
                if node.KindValue == kind)
    off_axis = max(sorted(map(abs, vector))[1] for vector in carriers)
    return {"partition_sha256": sha256(stream).hexdigest(), "active_sha256": active.sha256, "history_sha256": history.sha256,
            "replayed_full_partition_bytes": True, "active_node_count": len(nodes),
            "body_match_tag": tag, "producer_id": feature_id, "body_atom_id": atom_id,
            "active_mark": active_mark, "prior_mark": prior_mark, "rollback_deleted_records": len(selected.rollback.deleted),
            "actual_axis_coordinates_mm": actual_stations, "maximum_off_axis_carrier_component": off_axis,
            "rollback_contains_previous_edited_solid": False,
            "entities": compare_saved_nodes(nodes, raw_roles, portable, cold_owners)}
