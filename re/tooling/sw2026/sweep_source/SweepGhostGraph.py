from collections import Counter
from math import dist
from struct import pack

from convert.Geometry.Parasolid import DecodePartData, EncodePartData, KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import WriteXmtEndMut
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from SweepArchiveOwners import NativeNodeId, RequireNative, one
from SweepModel import require


GHOST_STREAM = "Contents/Config-0-GhostPartition"
DESCRIPTION = b": TRANSMIT FILE (partition) created by modeller version 3701250"
BODY_KEY = "GHOST_REF_BODY_ID_2001"
EDGE_KEY = "EDGE_ID_2001"


def reference_owner(link, wrapper, profile):
    reference = RequireNative(wrapper.FieldsValue["f58"], "moCompProfile_c")
    unit = RequireNative(reference.FieldsValue["f58"], "moUnitComponent_c")
    require(unit.FieldsValue == {"owner": link.ConfigValue.RootValue, "has_ext": 0}
            and sum(node is profile for node in link.ResolvedValue.RootsValue) == 1, "unowned component selection")
    identifier = NativeNodeId(profile)
    epoch = DatumTime(link.ConfigValue.HeaderValue, identifier)
    require(reference.FieldsValue["ff0"] == {"f00": identifier, "f08": epoch}, "ghost picker lost actual creation identity")
    shared = CompRefFields(unit)
    require(reference.FieldsValue.keys() == shared.keys() | {"ff0"}
            and all(reference.FieldsValue[name] == value for name, value in shared.items() if name not in ("f20", "f58")),
            "saved component selection changes another shared constructor field")
    return {"node": reference.IndexValue, "feature_id": identifier, "creation_epoch": epoch,
            "ghost_id": reference.FieldsValue["f20"], "general_flags": wrapper.FieldsValue["f08"],
            "general_secondary": wrapper.FieldsValue["f0c"], "general_embedded": wrapper.FieldsValue["has_fc8"]}


def component_roles(link, sweep, section, path):
    data = sweep.FieldsValue["f820"]
    section_curve = one(data["f2c0"])
    path_curve = one(data["f2e0"]).FieldsValue["fe8"]
    return {role: reference_owner(link, wrapper, profile)
            for role, wrapper, profile in (("section", section_curve, section), ("path", path_curve, path))}


def manager_rows(root, sweep, roles):
    manager = root.FieldsValue["fd90"]
    objects = tuple(item["o"] for item in manager["objects"])
    require(manager["n"] == len(objects) == len(roles) == 2 and manager["fe0"] == 2,
            "disclosed ghost manager uses an alternate population or partition state")
    indices = tuple(item["f08"] for item in objects)
    require(indices == (roles["path"]["ghost_id"], roles["section"]["ghost_id"])
            and indices == (manager["f80"], manager["f80"] - 1), "ghost manager order or last allocation differs")
    for item in objects:
        require((item["f0c"], item["f10"], item["fc0"], item["nb0"], item["has_f50"], item["nf0"])
                == (8, 0, -1, 1, 0, 0) and not item["ff0"] and item.get("f50") is None
                and item["fa0"] == [{"v": NativeNodeId(sweep)}], "ghost record does not identify its actual sweep user")
    return {"last_id": manager["f80"], "packed_flags": manager["fe0"], "rows_in_order": list(indices),
            "parent_feature_id": NativeNodeId(sweep)}


def follow(nodes, node, field, kind):
    value = nodes[node.Integer(field)]
    require(value.KindValue == kind, f"ghost {field} points to the wrong kernel kind")
    return value


def attribute(nodes, owner, identifier):
    value = follow(nodes, owner, "attributes_features", 81)
    definition = follow(nodes, value, "definition", 80)
    name = follow(nodes, definition, "identifier", 79).FieldsValue["string"]
    require(value.Integer("owner") == owner.IndexValue and name == identifier,
            "ghost body or rim attribute lost its actual typed owner")
    return value


def body_ghost_id(nodes, body):
    fields = attribute(nodes, body, BODY_KEY).FieldsValue["fields"]
    require(len(fields) == 2 and fields[0] == 0 and nodes[fields[1]].KindValue == 82, "unexpected ghost ID attribute")
    result, = nodes[fields[1]].FieldsValue["values"]
    return result


def observe_path(nodes, body, model):
    shell = follow(nodes, body, "shell", 13)
    edge = follow(nodes, shell, "edge", 16)
    curve = follow(nodes, edge, "curve", 31)
    positive = follow(nodes, edge, "halfedge", 17)
    negative = follow(nodes, positive, "other", 17)
    vertices = (follow(nodes, positive, "vertex", 18), follow(nodes, negative, "vertex", 18))
    require(shell.Integer("body") == body.IndexValue and edge.Integer("owner") == shell.IndexValue
            and curve.Integer("owner") == edge.IndexValue and negative.Integer("other") == positive.IndexValue
            and all(node.Integer("edge") == edge.IndexValue and node.Integer("loop") == 0 for node in (positive, negative))
            and positive.FieldsValue["sense"] == "+" and negative.FieldsValue["sense"] == "-"
            and all(vertex.Integer("owner") == body.IndexValue for vertex in vertices)
            and (body.Integer("edge"), shell.Integer("face")) == (0, 0), "ghost path incidence differs")
    points = tuple(follow(nodes, vertex, "point", 29) for vertex in vertices)
    actual = tuple(point.FieldsValue["pvec"] for point in points)
    require(all(point.Integer("owner") == vertex.IndexValue for point, vertex in zip(points, vertices, strict=True))
            and actual[0] == tuple(model["arc"]["end_m"]) and dist(actual[1], model["arc"]["start_m"]) < 1e-16
            and (curve.FieldsValue["radius"], curve.FieldsValue["centre"], curve.FieldsValue["normal"])
            == (model["driver"]["metres"], tuple(model["arc"]["center_m"]), (0, 0, 1)),
            "ghost path is not the actual edited Front arc")
    return {"body": body.IndexValue, "edge": edge.IndexValue, "radius_m": curve.FieldsValue["radius"],
            "arc_points_end_start_m": actual}


def observe_section(nodes, body, model):
    shell = follow(nodes, body, "shell", 13)
    edge = follow(nodes, body, "edge", 16)
    curve = follow(nodes, edge, "curve", 31)
    face = follow(nodes, shell, "face", 14)
    plane = follow(nodes, face, "surface", 50)
    require(shell.Integer("body") == body.IndexValue and face.Integer("shell") == shell.IndexValue
            and face.Integer("front_shell") == shell.IndexValue and plane.Integer("owner") == face.IndexValue
            and edge.Integer("owner") == body.IndexValue and curve.Integer("owner") == edge.IndexValue
            and body.Integer("vertex") == 0 and all(value == (0, 0, 0) for value in (curve.FieldsValue["centre"], plane.FieldsValue["pvec"]))
            and curve.FieldsValue["radius"] == model["driver"]["metres"] / 2
            and curve.FieldsValue["normal"] == plane.FieldsValue["normal"] == (1, 0, 0),
            "ghost section is not the actual diameter-driven Right sheet")
    require(attribute(nodes, edge, EDGE_KEY).FieldsValue["fields"] == (0, 0), "unqualified section edge attribute")
    return {"body": body.IndexValue, "edge": edge.IndexValue, "face": face.IndexValue, "radius_m": curve.FieldsValue["radius"]}


def encode_ghost(nodes):
    buffer = bytearray(pack(">HI", 239, 0))
    seen = set()
    for node in nodes.values():
        WriteXmtNodeMut(buffer, node, KKernelShapes[node.KindValue], seen)
    WriteXmtEndMut(buffer)
    return ParaStream(buffer, KTerminalFinSchema, DESCRIPTION)


def inspect_ghost(raw, roles, owners):
    payload, = DecodePartData(raw, GHOST_STREAM)
    require(payload.wrapper_offset == 0 and payload.stored_size == len(raw), "ghost partition has extra outer owners")
    nodes = ReadActiveNodes(payload.data)
    world, = (node for node in nodes.values() if node.KindValue == 101)
    path = follow(nodes, world, "body", 12)
    section = follow(nodes, path, "next", 12)
    require(Counter(node.KindValue for node in nodes.values())[12] == 2 and path.Integer("body_type") == 2
            and section.Integer("body_type") == 3 and section.Integer("next") == path.Integer("previous") == 0
            and section.Integer("previous") == path.IndexValue and path.Integer("owner") == section.Integer("owner") == world.IndexValue
            and all(body_ghost_id(nodes, node) == roles[role]["ghost_id"] for role, node in (("path", path), ("section", section))),
            "world does not bind its sweep ghost path and section")
    reemitted = encode_ghost(nodes)
    require(reemitted == payload.data and EncodePartData(reemitted) == raw, "typed ghost transmit did not replay exactly")
    path = observe_path(nodes, path, owners["path"])
    require(attribute(nodes, nodes[path["edge"]], EDGE_KEY).FieldsValue["fields"] == (0, 0), "unqualified path edge attribute")
    return {"path": path, "section": observe_section(nodes, section, owners["section"]),
            "kernel_sha256": payload.sha256, "kernel_bytes": len(reemitted), "wrapped_bytes": len(raw),
            "typed_nodes": len(nodes), "world_last_id": world.Integer("highest_id"), "raw_and_wrapper_exact": True}


def read_ghost(archive, roles, owners):
    return inspect_ghost(archive.require(GHOST_STREAM), roles, owners)
