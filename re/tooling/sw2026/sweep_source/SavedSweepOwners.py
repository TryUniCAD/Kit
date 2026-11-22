from math import ulp

from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Container.Format import KConfigStream, KPartitionStream, KResolvedFeaturesStream
from convert.adapters.solidworks.Container.Parasolid import decode_brep_model
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwArc import ReadSwArc, SwArcPoints
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwDriver import ReadSwDriver
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import ReadSwPick
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface, TorusSurface
from interchange.brep.Validation.BrepValidate import GetBrepErrors


def demand(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def by_type(graph, name):
    return tuple(node for entry in graph.MapValue.EntriesValue
                 if isinstance(node := entry.EntryValue, ArchiveNode) and node.ClassValue.NameValue == name)


def refs(container):
    rows = container["items"]
    demand(len(rows) == container["n"], "wrong saved archive object count")
    return tuple(row["o"] for row in rows)


def span(node):
    return {"map": node.IndexValue, "span": [node.StartOffset, node.EndOffset],
            "class": node.ClassValue.NameValue, "schema": node.ClassValue.SchemaValue}


def map_signature(graph):
    return tuple((entry.IndexValue,
                  span(value) if isinstance(value := entry.EntryValue, ArchiveNode) else repr(value))
                 for entry in graph.MapValue.EntriesValue)


def manager_owner(manager, replay, body_id):
    (linked,) = by_type(manager, "moLinkedAtomIdNode_c")
    fields = linked.FieldsValue
    compare = ReadCmgrMut(replay, 19000)
    demand(manager.RootValue.FieldsValue["f658"] == 1 and manager.MapValue.CounterValue == 19
           and map_signature(manager) == map_signature(compare)
           and fields["f08"] == body_id and all(not fields[name] for name in ("ff0", "f100", "f110", "f120")),
           "saved manager map does not preserve its one measured link and separate suffix")
    return {"f658": 1, "body_id": body_id, "linked_atom": span(linked), "inline_mbs_count": 0}


def history_owners(config, resolved, features):
    items = by_type(resolved, "moHistoryFeatItemData_c")
    (folder,) = (node for node in resolved.RootsValue if node.ClassValue.NameValue == "moHistoryFolder_c")
    demand(refs(folder.FieldsValue["f3c8"]) == items and len(items) == 3,
           "history folder does not own the three reached references")
    result = []
    for item, feature in zip(items, features, strict=True):
        component = item.FieldsValue["f48"]
        data = component.FieldsValue
        feature_id = NativeNodeId(feature)
        demand(data["ff0"] == {"f00": feature_id, "f08": DatumTime(config.HeaderValue, feature_id)}
               and data["f58"].FieldsValue["owner"] is config.RootValue and data["f20"] == 0,
               "saved history child does not name its earlier local feature")
        result.append({"item": span(item), "component": span(component), "feature_id": feature_id})
    return result


def body_owners(config, resolved, sweep):
    fields = sweep.FieldsValue
    chooser = fields["f4a8"]
    (selection,) = refs(chooser["f48"])
    faces = refs(selection.FieldsValue["f08"])
    sides = tuple(
        node for face in faces for row in face.FieldsValue["f10"]
        if (node := row["f08"]) is not None and node.ClassValue.NameValue == "moSweepSideSurfIdRep_c"
    )
    expected_sides = by_type(resolved, "moSweepSideSurfIdRep_c")
    demand(chooser["f68"] is sweep and len(faces) == len(sides) == 2 and sides == expected_sides
           and all(row.FieldsValue["f10"]["f10"].FieldsValue["f10"]["f00"] == NativeNodeId(sweep)
                   and (row.FieldsValue["f38"], row.FieldsValue["f3c"]) == (1, 1) for row in expected_sides),
           "saved body selection does not retain its two actual side references")
    (atom,) = refs(fields["f528"])
    body_id = atom.FieldsValue["f140"]
    demand(by_type(config, "moAtom_c") == (atom,) and fields["f498"] == [{"v": body_id}]
           and atom.FieldsValue["f130"] == atom.FieldsValue["f12c"] == NativeNodeId(sweep)
           and fields["has_f548"] == 0 and fields["f544"] == 1,
           "saved swept boss has an alternate live body owner")
    return {"atom": {**span(atom), "id": body_id}, "side_reps": [span(row) for row in expected_sides],
            "per_body_chooser": span(selection), "face_references": [span(row) for row in faces],
            "result_ids": [body_id]}


def driver_owner(feature, is_section, expected):
    sketch = feature.FieldsValue["pd_f80"]
    driver = ReadSwDriver(sketch, is_section)
    demand(driver.MetresValue == expected, "typed driver differs from its pre-existing authored measurement")
    display, = refs(sketch.FieldsValue["dims"]["f118"].FieldsValue)
    positions = tuple((point.x, point.y) for point in SwArcPoints(sketch))
    radius = driver.MetresValue / 2 if is_section else driver.MetresValue
    try:
        ReadSwArc(sketch, radius, is_section)
    except ValueError as error:
        cold_incidence = str(error)
    else:
        cold_incidence = "matched"
    return {"feature_id": NativeNodeId(feature), "parameter": span(driver.ParameterValue),
            "dimension": span(driver.DimensionValue), "display": span(display),
            "persistent_dimension_id": driver.NativeId, "metres_hex": driver.MetresValue.hex(),
            "display_f2b0": [row["v"] for row in display.FieldsValue["f2b0"]],
            "actual_points_m": positions, "cold_incidence": cold_incidence}


def physical_result(archive, atom_id, drivers):
    partition, deltas = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    demand(" (partition) " in ParaHeaderData(partition.data).description
           and " (deltas) " in ParaHeaderData(deltas.data).description, "wrong saved partition roles")
    model = decode_brep_model(partition.data)
    demand(model is not None and not GetBrepErrors(model, frozenset()) and
           (len(model.bodies), len(model.regions), len(model.shells), len(model.faces),
            len(model.edges), len(model.vertices)) == (1, 1, 1, 3, 2, 2)
           and model.regions[0].solid and model.shells[0].closed,
           "saved result does not expose its actual closed B-rep")
    identity = ReadShellAtom(partition.data, model)
    demand(identity["body_atom_id"] == atom_id, "foreign physical result atom")
    torus, = (value for value in model.surfaces if type(value) is TorusSurface)
    planes = tuple(value for value in model.surfaces if type(value) is PlaneSurface)
    observed = (torus.major_radius, torus.minor_radius)
    expected = (1000 * drivers[1], 500 * drivers[0])
    deltas_ulp = tuple((seen - wanted) / ulp(wanted) for seen, wanted in zip(observed, expected, strict=True))
    demand(all(abs(value) <= 1 for value in deltas_ulp) and len(planes) == 2
           and tuple((row.same_sense, len(row.loop_ids)) for row in model.faces)
           == ((False, 1), (True, 1), (True, 2)), "physical result carrier differs from the actual drivers")
    return {**identity, "partition_sha256": partition.sha256, "deltas_sha256": deltas.sha256,
            "radii_mm": observed, "radius_display_delta_ulp": deltas_ulp, "counts": [1, 3, 2, 2],
            "full_kernel_boundary": kernel_boundary(partition.data),
            "coedges": len(model.coedges), "stored_pcurves_exposed_by_sdk": len(model.pcurves)}


def kernel_boundary(raw):
    header = ParaHeaderData(raw)
    reader = XmtCursor(raw[header.body_offset:])
    objects = 0
    while (kind := reader.ReadKind()) != 1:
        body_offset = header.body_offset + reader.OffsetValue
        try:
            ReadXmtNodeMut(reader, kind)
        except ValueError as error:
            return {"next_kind": kind, "read_objects": objects, "diagnostic": str(error),
                    "kind_offset": body_offset - 2, "body_offset": body_offset}
        objects += 1
    reader.FinishRead()
    return {"read_objects": objects, "complete": True}


def semantic_owners(archive, config, manager, resolved, drivers):
    (sweep,) = by_type(resolved, "moSweep_c")
    section, path = ReadParents(sweep)
    demand(resolved.RootsValue[-3:] == (section, path, sweep), "saved sweep does not reference its actual roots")
    data = sweep.FieldsValue["f820"]
    (picked_section,) = refs(data["f2c0"])
    (contact,) = refs(data["f2e0"])
    picked_path = contact.FieldsValue["fe8"]
    link = NativeLink(config, resolved, KConfigStream, KResolvedFeaturesStream, manager)
    ghost_ids = (ReadSwPick(link, picked_section, section), ReadSwPick(link, picked_path, path))
    demand(len(set(ghost_ids)) == 2 and (data["f2b4"], data["f2b8"], data["f2a0"]) == (1, 1, None)
           and not any(data[name] for name in ("f7c", "f80", "f234", "f258", "f278")),
           "saved sweep has alternate or unresolved Standard options")
    body = picked_section.FieldsValue["fc8"]
    carrier, = (node for node in body["resident_nodes"] if node.KindValue == 31)
    demand(picked_path.FieldsValue["has_fc8"] == 0 and carrier.FieldsValue["radius"] == drivers[0] / 2,
           "embedded sheet does not belong to the live Section diameter")
    binding = body_owners(config, resolved, sweep)
    return {**binding, "feature": span(sweep), "feature_id": NativeNodeId(sweep), "picked_ghost_ids": ghost_ids,
            "section_sheet": {"span": body["span"], "sha256": body["payload_sha256"],
                              "nonresident_next": 2, "resident_nodes": len(body["resident_nodes"])},
            "warm_words": {"f2b4": 1, "f2b8": 1}, "history": history_owners(config, resolved, (section, path, sweep)),
            "drivers": [driver_owner(section, True, drivers[0]), driver_owner(path, False, drivers[1])],
            "physical_result": physical_result(archive, binding["atom"]["id"], drivers)}
