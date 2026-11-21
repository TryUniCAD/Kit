from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import product
from json import dumps
from math import dist, fsum, isclose, prod
from pathlib import Path
from sys import addaudithook, path as module_path

module_path.insert(0, str(Path(__file__).resolve().parents[1] / "serial"))

from Classes import registry
from Core import DOCUMENT_VERSION_2026, Obj
from builders.EmptyPartition import SOLIDWORKS_2026
from convert.Geometry.Parasolid import DecodeBrepModel, DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from para.Partition import frame_payloads, read_partition, write_payloads
from para.Schema import SCHEMAS
from para.Tracking import FILETIME_TICKS_PER_SECOND, FILETIME_UNIX_EPOCH, local_downstream_face_words, unchanged_face_stamp


STREAM = "Contents/Config-0-Partition"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def difference(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return fsum(x * y for x, y in zip(a, b, strict=True))


def measure(points, faces, bounds):
    lower, upper = bounds[:3], bounds[3:]
    corners = tuple(product(*zip(lower, upper, strict=True)))
    dimensions = difference(upper, lower)
    require(all(value > 0 for value in dimensions), "rectangle bounds must have positive extents")
    close = lambda a, b: isclose(a, b, rel_tol=1e-12, abs_tol=1e-9)
    matching = [{index for index, corner in enumerate(corners) if dist(corner, point) < 1e-9} for point in points]
    require(len(matching) == 8 and all(len(members) == 1 for members in matching)
            and len(set.union(*matching)) == 8, "points do not match the eight expected corners")
    center = tuple((lo + hi) / 2 for lo, hi in zip(lower, upper, strict=True))
    area = []
    tetrahedra = []
    directions = []
    sided_planes = set()
    oriented_edges = Counter()
    for ring in faces:
        require(len(ring) == 4 and len(set(ring)) == 4, "rectangle face is not a quad")
        for start, end in zip(ring, ring[1:] + ring[:1], strict=True):
            oriented_edges[start, end] += 1
            require(sum(not close(a, b) for a, b in zip(start, end, strict=True)) == 1, "rectangle edge changes more than one axis")
        axis, = [i for i, values in enumerate(zip(*ring, strict=True)) if all(close(values[0], value) for value in values)]
        sided_planes.add((axis, ring[0][axis] > center[axis]))
        head, b, c, d = ring
        oriented = cross(difference(b, head), difference(c, head))
        direction = dot(oriented, difference(head, center))
        require(direction != 0, "rectangle face has zero oriented area")
        directions.append(1 if direction > 0 else -1)
        for left, right in ((b, c), (c, d)):
            area.append(dist(cross(difference(left, head), difference(right, head)), (0, 0, 0)) / 2)
            volume = dot(head, cross(left, right)) / 6
            tetrahedra.append((volume, tuple((a + b + c) / 4 for a, b, c in zip(head, left, right, strict=True))))
    require(len(sided_planes) == len(faces) == 6 and len(oriented_edges) == 24
            and all(count == oriented_edges[end, start] == 1
                    for (start, end), count in oriented_edges.items()), "face adjacency does not close a rectangle")
    volume = fsum(value for value, _ in tetrahedra)
    measured_center = tuple(fsum(value * point[i] for value, point in tetrahedra) / volume for i in range(3))
    a, b, c = dimensions
    require(close(abs(volume), prod(dimensions)) and close(fsum(area), 2 * (a*b + a*c + b*c))
            and all(close(got, expected) for got, expected in zip(measured_center, center, strict=True)),
            "rectangle topology disagrees with the independent size and centroid")
    return {"area_mm2": fsum(area), "signed_volume_mm3": volume, "center_mm": measured_center,
            "bounds_mm": [lower, upper], "loop_direction": directions}


def node_lookup(partition):
    nodes = {node.index: node for node in partition.nodes}

    def fields(index, kind):
        node = nodes[index]
        require(node.kind == kind, f"node {index} is {SCHEMAS[node.kind].name}, expected {SCHEMAS[kind].name}")
        return node.fields

    return nodes, fields


def native_geometry(partition, bounds):
    nodes, fields = node_lookup(partition)
    counts = Counter(SCHEMAS[node.kind].name for node in nodes.values())
    require(all(counts[name] == count for name, count in {
        "BODY": 1, "REGION": 2, "SHELL": 2, "FACE": 6, "LOOP": 6, "EDGE": 12, "HALFEDGE": 24,
        "VERTEX": 8, "POINT": 8, "LINE": 12, "PLANE": 6,
    }.items()), "current partition topology is outside the ordinary rectangle cohort")
    body_index = fields(1, 101)["body"]
    body = fields(body_index, 12)
    void = fields(body["region"], 19)
    solid = fields(void["next"], 19)
    require((void["type"], solid["type"]) == ("V", "S") and not solid["next"]
            and solid["previous"] == body["region"] and void["body"] == solid["body"] == body_index
            and body["shell"] == solid["shell"]
            and fields(void["shell"], 13)["region"] == body["region"]
            and fields(solid["shell"], 13)["region"] == void["next"],
            "rectangle interior and exterior uses are disconnected")
    points = {
        node.index: tuple(1000 * value for value in fields(node.fields["point"], 29)["pvec"])
        for node in nodes.values() if node.kind == 18
    }
    faces = []
    all_fins = set()
    use_counts = Counter()
    for face in (node for node in nodes.values() if node.kind == 14):
        topology = face.fields
        require(topology["shell"] == solid["shell"] and topology["front_shell"] == void["shell"],
                "face does not belong to both bounding shells")
        loop_index = topology["loop"]
        loop = fields(loop_index, 15)
        require(loop["face"] == face.index and not loop["next"], "rectangle face must own one loop")
        index = loop["halfedge"]
        ring = []
        for _ in range(4):
            require(index not in all_fins, "face loops share a directed edge use")
            all_fins.add(index)
            fin = fields(index, 17)
            mate = fields(fin["other"], 17)
            following = fields(fin["forward"], 17)
            require(fin["loop"] == loop_index and mate["other"] == index and following["backward"] == index
                    and mate["edge"] == fin["edge"] and fin["sense"] != mate["sense"]
                    and fin["vertex"] == fields(following["other"], 17)["vertex"],
                    "native fin/mate endpoints or owners disagree")
            line = fields(fields(fin["edge"], 16)["curve"], 30)
            start, finish = points[mate["vertex"]], points[fin["vertex"]]
            origin = tuple(1000 * value for value in line["pvec"])
            require(all(dist(cross(difference(point, origin), line["direction"]), (0, 0, 0)) < 1e-9
                        for point in (start, finish)), "native line does not support its endpoints")
            use_counts[fin["edge"]] += 1
            ring.append(start)
            index = fin["forward"]
        require(index == loop["halfedge"], "native rectangle loop is open")
        plane = fields(topology["surface"], 50)
        origin = tuple(1000 * value for value in plane["pvec"])
        require(all(abs(dot(difference(point, origin), plane["normal"])) < 1e-9 for point in ring),
                "native plane does not support all its boundary vertices")
        tessellated_normal = cross(difference(ring[1], ring[0]), difference(ring[2], ring[0]))
        surface_sign = 1 if plane["sense"] == topology["sense"] else -1
        require(surface_sign * dot(tessellated_normal, plane["normal"]) > 0, "native fin walk and face sense disagree")
        faces.append(tuple(ring))
    require(len(use_counts) == 12 and all(count == 2 for count in use_counts.values()), "edge uses do not form a closed manifold")
    return measure(tuple(points.values()), faces, bounds)


def ownership(partition):
    nodes, fields = node_lookup(partition)
    counts = Counter()
    attribute_sets = {}
    attr_heads = {}
    for node in nodes.values():
        if node.kind != 81:
            continue
        record = node.fields
        definition = fields(record["definition"], 80)
        name = fields(definition["identifier"], 79)["string"]
        field_types = {1: 82, 2: 83, 10: 98}
        values = tuple(
            fields(index, field_types[code])["values"] if index else None
            for code, index in zip(definition["fields"], record["fields"], strict=True)
        )
        counts[SCHEMAS[nodes[record["owner"]].kind].name, name] += 1
        attribute_sets.setdefault(name, []).append(values)
        if not record["previous_of_type"]:
            require(record["definition"] not in attr_heads, "attribute definition has multiple per-body chain heads")
            attr_heads[record["definition"]] = node.index
        for previous, following, owner in (("previous", "next", "owner"), ("previous_of_type", "next_of_type", "definition")):
            if index := record[following]:
                neighbor = fields(index, 81)
                require(neighbor[previous] == node.index and neighbor[owner] == record[owner], "attribute chain is not reciprocal")
    if not counts:
        return {}
    body_index = fields(1, 101)["body"]
    chain_list = fields(fields(body_index, 12)["attribute_chains"], 70)
    block = fields(chain_list["list_block"], 74)
    entries = block["entries"]
    count = block["n_entries"]
    require(chain_list["owner"] == body_index and chain_list["finger_block"] == chain_list["list_block"]
            and count == chain_list["list_length"] and chain_list["block_length"] == len(entries)
            and count == len(attr_heads) and set(entries[:count]) == set(attr_heads.values())
            and not any(entries[count:]), "attribute block does not contain one head per definition")
    stamp_words = [record[0][0] & 0xffffffff for record in attribute_sets["SWEntUnchanged"]]
    downstream = attribute_sets["DOWNSTREAM_FACE_ID"]
    require(len(downstream) == 6 and len(set(downstream)) == 1
            and all(len(record[0]) == 6 and record[1:] == (None, None) for record in downstream),
            "ordinary rectangle faces do not use one local downstream time")
    words = downstream[0][0]
    filetime = ((words[2] & 0xffffffff) << 32) | (words[1] & 0xffffffff)
    seconds, fraction = divmod(filetime - FILETIME_UNIX_EPOCH, FILETIME_TICKS_PER_SECOND)
    require(local_downstream_face_words(seconds, fraction) == words, "downstream time words do not follow the local face layout")
    require(all(unchanged_face_stamp(word >> 16, word & 0xffff) & 0xffffffff == word for word in stamp_words),
            "face tags and configuration stamps do not reconstruct the stored words")
    return {
        "attributes_by_owner": {f"{owner}.{name}": count for (owner, name), count in sorted(counts.items())},
        "body_match_tag": attribute_sets["BODY_MATCH"][0][0][0],
        "body_stamp": attribute_sets["ENT_TIME_STAMP_2001"][0][1][0],
        "atom_id": attribute_sets["ATOM_ID_2001"][0][1][0],
        "last_modifying_feature": attribute_sets["LAST_BODY_MODIFYING_FEATURE_ID"][0][1][0],
        "configuration_stamp_low16": sorted({word & 0xffff for word in stamp_words}),
        "face_tags_low16": sorted(word >> 16 for word in stamp_words),
        "downstream_updated_at": seconds,
        "downstream_subsecond_ticks": fraction,
    }


def vector(value):
    return (value.x, value.y, value.z)


def sdk_geometry(payload, bounds):
    model = DecodeBrepModel(payload)
    require(model is not None and not model.validate(), "SDK did not decode a valid rectangle model")
    vertices = {vertex.id: vector(vertex.point) for vertex in model.vertices}
    loops = {loop.id: loop for loop in model.loops}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    edges = {edge.id: edge for edge in model.edges}
    faces = []
    for face in model.faces:
        loop_id, = face.loop_ids
        ring = []
        for coedge_id in loops[loop_id].coedge_ids:
            coedge = coedges[coedge_id]
            edge = edges[coedge.edge_id]
            ring.append(vertices[edge.end_vertex_id if coedge.reversed else edge.start_vertex_id])
        faces.append(tuple(ring))
    result = measure(tuple(vertices.values()), faces, bounds)
    result.update(body_count=len(model.bodies), shell_count=len(model.shells), region_count=len(model.regions))
    return result


def archive_binding(archive):
    config_name = "Contents/Config-0"
    resolved_name = config_name + "-ResolvedFeatures"
    reg = registry()
    document, reader = load_config(archive.require(config_name), reg, DOCUMENT_VERSION_2026,
                                   archive=archive, name=config_name)
    features, feature_reader = load_resolved(archive.require(resolved_name), reg, DOCUMENT_VERSION_2026,
                                             archive=archive, name=resolved_name, seed=reader.map_state())
    require(not document.tail and not features.tail, "archive has unread model or feature fields")
    model, = document.roots
    extrusion, = (node for node in features.roots if isinstance(node, Obj) and node.cls == "moExtrusion_c")
    atoms = {
        id(row[1]): row[1] for state in (reader, feature_reader) for row in state.table.values()
        if row[0] == "obj" and row[1].cls == "moAtom_c"
    }
    active = document.head["model_header"]
    activation_mark = model.f.get("fe38")
    feature_mark = extrusion.f.get("f3d0")
    return {
        "header_update_stamp": active["f40"],
        "header_updated_at": active["f48"],
        "header_body_stamp": active["f44"],
        "feature_update_stamp": extrusion["f29c"],
        "feature_id": extrusion["f08"],
        "model_activation_mark": activation_mark["f18"] if activation_mark else None,
        "feature_mark": feature_mark["f18"] if feature_mark else None,
        "atoms": [{key: node[key] for key in ("f140", "f12c", "f130", "f180", "f1b0", "f19c")} for node in atoms.values()],
    }


def inspect_binding(partition, owners, binding):
    marks = {entry.mark.index: entry.mark for entry in partition.history}
    current_mark = marks[partition.root.fields["current_pmark"]]
    preceding_mark = marks[current_mark.fields["preceding"]]
    atom, = binding["atoms"]
    require(atom["f180"] == atom["f1b0"] == owners["body_match_tag"] and atom["f140"] == owners["atom_id"]
            and atom["f12c"] == atom["f130"] == binding["feature_id"] == owners["last_modifying_feature"]
            and atom["f19c"] == owners["attributes_by_owner"]["FACE.FACE_ID_2001"]
            and binding["feature_mark"] == current_mark.fields["id"]
            and binding["model_activation_mark"] == preceding_mark.fields["id"]
            and binding["header_body_stamp"] == owners["body_stamp"]
            and binding["header_updated_at"] == owners["downstream_updated_at"],
            "archive model owners do not agree with the kernel graph")
    current_rollback, = (entry.rollback for entry in partition.history if entry.mark is current_mark)
    live = {node.index for node in partition.nodes if node.kind not in (79, 80, 101)}
    require(current_rollback is not None and {index for index, _ in current_rollback.deleted} == live,
            "ordinary rectangle geometry rollback excludes an unexpected active node")


def compare(path, bounds, audit):
    archive_bytes = path.read_bytes()
    archive = SldprtArchive.from_bytes(archive_bytes, path)
    stream = archive.require(STREAM)
    payloads = DecodePartData(stream)
    report = {"file": path.name, "source_sha256": sha256(archive_bytes).hexdigest(),
              "stream_sha256": sha256(stream).hexdigest(), "stream_bytes": len(stream),
              "payloads": [{"schema": part.schema, "kind": part.kind, "bytes": len(part.data), "sha256": part.sha256}
                           for part in payloads]}
    if payloads[0].schema != SOLIDWORKS_2026.schema:
        require(len(payloads) == 1 and payloads[0].schema == "SCH_1200000_12006",
                "only the earlier unadorned prism comparator is supported")
        report["sdk_geometry"] = sdk_geometry(payloads[0].data, bounds)
        report["archive_binding"] = archive_binding(archive)
        return report
    partition = read_partition(stream)
    audit["enabled"] = True
    before = audit["opens"]
    try:
        regenerated = write_payloads(partition)
        frame = frame_payloads(regenerated)
    finally:
        audit["enabled"] = False
    require(all(data == saved.data for data, saved in zip(regenerated, payloads, strict=True)),
            "regenerated payload differs")
    require(frame == stream and audit["opens"] == before, "regenerated framing differs or emission opened a file")
    report.update({
        "exact_payloads": True, "exact_framing": True, "emission_file_opens": audit["opens"] - before,
        "node_counts": dict(sorted(Counter(SCHEMAS[node.kind].name for node in partition.nodes).items())),
        "effective_schema_edits": sorted({SCHEMAS[node.kind].name for node in partition.nodes
                                         if SCHEMAS[node.kind].base != SCHEMAS[node.kind].current}),
        "history": [{"index": entry.mark.index, "id": entry.mark.fields["id"],
                     "key": entry.mark.fields["delta_key"], "new_count": entry.mark.fields["n_new_nodes"],
                     "deleted_refs": len(entry.rollback.deleted) if entry.rollback else None,
                     "prior_world_alive": bool(entry.rollback.previous_world.fields["alive"]) if entry.rollback else None}
                    for entry in partition.history],
    })
    if any(node.kind == 12 for node in partition.nodes):
        report["wire_geometry"] = native_geometry(partition, bounds)
        report["sdk_geometry"] = sdk_geometry(payloads[0].data, bounds)
        report["ownership"] = owners = ownership(partition)
        report["archive_binding"] = binding = archive_binding(archive)
        inspect_binding(partition, owners, binding)
    return report


def main():
    parser = ArgumentParser()
    parser.add_argument("--bounds-mm", nargs=6, type=float, required=True,
                        metavar=("MIN_X", "MIN_Y", "MIN_Z", "MAX_X", "MAX_Y", "MAX_Z"))
    parser.add_argument("sources", nargs="+", type=Path)
    arguments = parser.parse_args()
    audit = {"enabled": False, "opens": 0}

    def opened(event, arguments):
        if audit["enabled"] and event == "open":
            audit["opens"] += 1

    addaudithook(opened)
    print(dumps([compare(path, arguments.bounds_mm, audit) for path in arguments.sources], indent=2))


if __name__ == "__main__":
    main()
