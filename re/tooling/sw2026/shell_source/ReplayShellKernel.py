from hashlib import sha256
from struct import pack

from convert.Geometry.Parasolid import ParaHeaderData, WritePointerMut
from convert.adapters.solidworks.Archive.Partition.History.ReadHistFrames import ReadHistFrames
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtDeltaMut import ReadXmtDeltaMut
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import ReadXmtStages
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.GetXmtField import GetXmtField
from convert.adapters.solidworks.Archive.Partition.LocalWrite.PutXmtValueMut import PutXmtValueMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import decode_partition_stream, encode_partition_stream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import ReadBodyLoop
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import ReadBodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadImplicitName import ReadImplicit

SCHEMA = "SCH_3701250_37102_13006"
PARTITION = "Contents/Config-0-Partition"
NORMAL_END = pack(">HH", 1, 1)
CAP = "moEndFaceSurfIdRep_c"
WALL = "moFromSktEntSurfIdRep_c"


def demand(ok, why):
    if not ok:
        raise ValueError(why)


def header(source, role):
    stored = ParaHeaderData(source)
    description = f": TRANSMIT FILE ({role}) created by modeller version 3701250"
    demand(stored is not None and (stored.description, stored.schema) == (description, SCHEMA),
           "unsupported kernel transmit envelope")
    text, schema = description.encode("ascii"), SCHEMA.encode("ascii")
    return bytearray(b"PS\0\0" + pack(">H", len(text)) + text + pack(">I", len(schema)) + schema + pack(">HI", 239, 0))


def write_node(output, node, kinds):
    WriteXmtNodeMut(output, node, KKernelShapes[node.KindValue], kinds)


def write_qualified(output, members, kinds, qualifiers):
    for node in members:
        shape = KKernelShapes[node.KindValue]
        fields = tuple((rule, GetXmtField(node, rule)) for rule in shape.FieldsValue)
        demand(len(fields) == len(node.FieldsValue), "rollback shape fields differ")
        output.extend(pack(">H", node.KindValue))
        if node.KindValue not in kinds:
            output.extend(SchemaHeader(shape))
            kinds.add(node.KindValue)
        for rule, (count, _) in fields:
            if rule.CountValue == 1:
                output.extend(pack(">I", count))
        WritePointerMut(output, node.IndexValue)
        for rule, (_, values) in fields:
            for value in values:
                PutXmtValueMut(output, rule.EncodingValue, value)
                if rule.EncodingValue == "p":
                    output.append(int(qualifiers[value]))
    output.extend(NORMAL_END)


def exact_transmit(active, history, nodes):
    active_output = header(active, "partition")
    kinds = set()
    for node in nodes.values():
        write_node(active_output, node, kinds)
    active_output.extend(NORMAL_END)
    demand(active_output == active, "active Parasolid graph does not re-emit exactly")
    root, marks, deltas = ReadHistFrames(history, nodes, ReadXmtDeltaMut)
    history_output = header(history, "deltas")
    spans = {}
    kinds = set()
    write_node(history_output, root, kinds)
    for index, mark in marks.items():
        write_node(history_output, mark, kinds)
        if index not in deltas:
            continue
        start = len(history_output)
        txn = deltas[index]
        write_qualified(history_output, txn.RestoredValue, kinds, txn.Qualifiers)
        for slot, kind in txn.RemovedValue:
            WritePointerMut(history_output, slot)
            history_output.extend(pack(">H", kind))
        WritePointerMut(history_output, 0)
        history_output.extend(pack(">i", txn.CopyCapacity))
        write_qualified(history_output, txn.PreviousValue, kinds, txn.Qualifiers)
        spans[index] = [start, len(history_output)]
    history_output.extend(NORMAL_END)
    demand(history_output == history, "retained Parasolid transactions do not re-emit exactly")
    return root, marks, spans, bytes(active_output), bytes(history_output)


def body_snapshot(nodes):
    world = RequireXmt(nodes, 1, 101)
    body = RequireXmt(nodes, world.Integer("body"), 12)
    attrs = ReadBodyAttrs(nodes, body)
    owner = attrs["SWIMPLICITBODYNAME_ID_U"]
    values = {label: ReadBodyScalar(nodes, attrs, label, index) for label, index in (
        ("BODY_MATCH", 0), ("ATOM_ID_2001", 1), ("LAST_BODY_MODIFYING_FEATURE_ID", 1), ("ENT_TIME_STAMP_2001", 1)
    )}
    return body, values | {"label": ReadImplicit(nodes, attrs),
                           "label_attribute": owner.IndexValue, "label_value": owner.Indexes("fields")[0]}


def face_keys(nodes, creator, event):
    faces = {}
    for face in (node for node in nodes.values() if node.KindValue == 14):
        attr = ReadBodyAttrs(nodes, face).get("FACE_ID_2001")
        if attr is None:
            continue
        slots = attr.Indexes("fields")
        demand(len(slots) == 4 and slots[:2] == (0, 0)
               and RequireXmt(nodes, attr.Integer("definition"), 80).Indexes("fields") == (9, 9, 1, 1),
               "stored historical face identity uses a different schema")
        value = RequireXmt(nodes, slots[2], 82).Indexes("values")
        if value[0] not in (40, 74) or value[1:3] != (creator, event):
            continue
        demand(len(value) == (6 if value[0] == 40 else 5), "historical face identity width differs")
        key = (CAP, value[4], value[5]) if value[0] == 40 else (WALL, value[4], None)
        demand(key not in faces, "historical face key is ambiguous within its mark")
        faces[key] = (face, attr.IndexValue)
    return faces


def prove_cap(stock_nodes, active_nodes, txn, facts):
    tree = ReadBodyTree(stock_nodes)
    lo, hi = facts["stock_bounds_metres"]
    corners = {(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])}
    vertices = {RequireXmt(stock_nodes, index, 29).FieldsValue["pvec"] for index in tree.PointIds}
    demand(vertices == corners, "restored stock does not match its actual profile and D1")
    owner = facts["creator_id"], facts["creator_time"]
    prior = face_keys(stock_nodes, *owner)
    keys = tuple(tuple(row) for row in facts["selected_carriers"])
    demand(set(prior) == (set(keys) | {(CAP, 0, 0)})
           and {node.IndexValue for node, _ in prior.values()} == set(tree.FaceIds),
           "restored stock carriers do not bind the typed chooser")
    cap, attribute = prior[keys[0]]
    rim, rim_attr = face_keys(active_nodes, *owner)[keys[0]]
    demand(cap.IndexValue not in active_nodes and any(node is cap for node in txn.RestoredValue)
           and rim.IndexValue != cap.IndexValue,
           "selected face does not have a distinct restored historical owner")
    loop, fins = ReadBodyLoop(stock_nodes, cap)
    cap_vertices = {
        RequireXmt(stock_nodes, RequireXmt(stock_nodes, RequireXmt(stock_nodes, index, 17).Integer("vertex"), 18).Integer("point"), 29).FieldsValue["pvec"]
        for index in fins
    }
    demand(cap_vertices == {point for point in corners if point[2] == hi[2]},
           "historical cap is not the actual top of the stock extrusion")
    rim_loops = WalkXmtChain(active_nodes, rim.Integer("loop"), 15, PreviousField=None, OwnerField="face", OwnerValue=rim.IndexValue)
    demand(len(rim_loops) == 2, "live face with the same key is not the active rim")
    return {
        "stock_body_slot": tree.BodyIndex,
        "stock_faces_edges_vertices": [len(tree.FaceIds), len(tree.EdgeIds), len(tree.VertexIds)],
        "restored_cap_slot": cap.IndexValue, "restored_cap_loop_slot": loop,
        "restored_cap_attribute_slot": attribute, "restored_cap_ordinal": keys[0][1],
        "same_key_active_rim_slot": rim.IndexValue, "same_key_active_attribute_slot": rim_attr,
        "active_rim_loop_count": len(rim_loops),
        "actual_stock_carriers": [{"role": key, "slot": node.IndexValue} for key, (node, _) in prior.items()],
    }


def stage_data(stages, spans, facts, bookkeeping):
    active, stock, activation, initial = stages
    live_nodes, stock_nodes = active.NodesValue, stock.NodesValue
    live, live_attrs = body_snapshot(live_nodes)
    prior, prior_attrs = body_snapshot(stock_nodes)
    effect, creation, start = active.UndoValue, stock.UndoValue, activation.UndoValue
    demand(effect is not None and creation is not None and start is not None and initial.UndoValue is None,
           "linked archive controllers do not own all past states")
    demand(live.IndexValue == prior.IndexValue
           and any(node is prior for node in effect.PreviousValue)
           and not any(kind == 12 for _, kind in effect.RemovedValue)
           and not any(node.KindValue == 12 for node in effect.RestoredValue)
           and [(slot, kind) for slot, kind in creation.RemovedValue if kind == 12] == [(prior.IndexValue, 12)]
           and not creation.RestoredValue and not start.RestoredValue and not start.RemovedValue,
           "earlier stock and active shell have different retained body ownership")
    for values, producer, name in (
        (live_attrs, facts["modifier_id"], facts["modifier_name"]),
        (prior_attrs, facts["creator_id"], facts["creator_name"]),
    ):
        demand(values["BODY_MATCH"] == facts["kernel_body_tag"] and values["ATOM_ID_2001"] == facts["atom_id"]
               and values["LAST_BODY_MODIFYING_FEATURE_ID"] == producer and values["label"] == name,
               "owned past body atom, label or producer differs")
    demand(live_attrs["ENT_TIME_STAMP_2001"] == bookkeeping["body"],
           "active time stamp differs from actual Header2 body counter")
    demand(effect.RestoredValue[0].IndexValue == prior_attrs["label_value"]
           and effect.RestoredValue[0].KindValue == 98 and (live_attrs["label_value"], 98) in effect.RemovedValue,
           "true previous label is missing from the restored rows")
    cap = prove_cap(stock_nodes, live_nodes, effect, facts)
    titles = ["shell", "stock", "activation", "initial"]
    inventory = []
    for title, stage in zip(titles, stages, strict=True):
        nodes, mark, delta = stage.NodesValue, stage.MarkValue, stage.UndoValue
        world = RequireXmt(nodes, 1, 101)
        expected_live = int(title != "initial")
        expected_body = live.IndexValue if title in ("shell", "stock") else 0
        demand(world.Integer("body") == expected_body and world.Integer("alive") == expected_live
               and sorted(node.IndexValue for node in nodes.values() if node.KindValue == 12)
               == ([expected_body] if expected_body else []),
               "past world does not own the expected historical body inventory")
        inventory.append({
            "stage": title, "mark": mark.Integer("id"), "mark_slot": mark.IndexValue, "delta_key": mark.Integer("delta_key"),
            "previous_slot": mark.Integer("preceding"), "next_slot": mark.Integer("first_following"),
            "node_count": len(nodes), "world": {name: world.Integer(name) for name in ("alive", "body", "current_id", "highest_id", "attrib_def")},
            "typed_transaction": None if delta is None else {
                "payload_span": spans[mark.IndexValue], "restored": len(delta.RestoredValue),
                "removed": len(delta.RemovedValue), "copied": len(delta.PreviousValue), "copy_capacity": delta.CopyCapacity,
                "header_counts": [mark.Integer(field) for field in ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")],
                "qualifier_slots": {flag: sum(value == bool(flag) for value in delta.Qualifiers.values()) for flag in (0, 1)},
            },
        })
    return {"body_slot": live.IndexValue, "active_attributes": live_attrs, "restored_attributes": prior_attrs,
            "cap": cap, "stages": inventory}


def read_kernel(raw, archive_facts):
    archive = SldprtArchive.from_bytes(raw)
    physical = archive.require(PARTITION)
    active, history = decode_partition_stream(physical, PARTITION)
    demand((active.kind, history.kind) == ("partition", "deltas"), "partition role order differs")
    nodes = ReadActiveNodes(active.data)
    root, marks, spans, active_wire, history_wire = exact_transmit(active.data, history.data, nodes)
    facts = archive_facts["owners"]
    stages = ReadXmtStages(history.data, nodes, tuple(facts["controller_marks"]))
    result = stage_data(stages, spans, facts, archive_facts["bookkeeping"])
    rebuilt = encode_partition_stream(active_wire) + encode_partition_stream(history_wire)
    demand(tuple(row.data for row in decode_partition_stream(rebuilt, PARTITION)) == (active.data, history.data),
           "reframed partition payloads differ")
    return result | {
        "schema": SCHEMA,
        "physical_mark_order": [mark.Integer("id") for mark in marks.values()],
        "partition_root_slot": root.IndexValue, "current_mark_slot": root.Integer("current_pmark"),
        "exact_uncompressed_replays": {"partition": active.sha256, "deltas": history.sha256},
        "source_transport": {"bytes": len(physical), "sha256": sha256(physical).hexdigest(),
                             "wrapper_offsets": [active.wrapper_offset, history.wrapper_offset]},
        "reframed_transport": {"same_uncompressed_payloads": True,
                               "source_bytes_equal": rebuilt == physical},
    }
