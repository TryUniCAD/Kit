from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from json import dumps
from math import isclose, prod
from pathlib import Path
from sys import addaudithook

from .Allocate import DeltaEvent, IncompletePartition, MarkEvent, Session, Update
from .Attributes import RECTANGLE_DEFINITION_BY_NAME
from .Geometry import plan_rectangle
from .RectangleAttributes import Appearance, feature_created_at
from .RectanglePartition import project_rectangle
from Classes import registry
from builders.Part import construct_part
from convert.adapters.solidworks.Container.Container import SldprtArchive
from para.CompareRectangle import native_geometry, ownership
from para.Partition import frame_payloads, read_partition, references, write_payloads
from para.Schema import SCHEMAS
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


def control(name, extents, features, dimensioned=False):
    lo_x, lo_y, hi_x, hi_y, depth = extents
    coords = ((lo_x, lo_y), (hi_x, lo_y), (hi_x, hi_y), (lo_x, hi_y))
    profile = [[value / 1000 for value in coords[index]] for index in features]
    request = MakePartInput(profile, depth / 1000, name)
    request["document"]["extrusion_name"] = "Rectangle " + name
    if dimensioned:
        request["document"]["rectangle_dimensions"] = {
            "width_text_m": [(lo_x + hi_x) / 2000, (lo_y - 4) / 1000],
            "height_text_m": [(hi_x + 4) / 1000, (lo_y + hi_y) / 2000],
            "route_centerline": False,
        }
    return construct_part(registry=registry(), **request)


def schedule(first_tag, first_delta, temp_before, temp_after, advance_before, advance_after, post_attach, seconds, fraction):
    steps = [DeltaEvent("geometry")]
    for i in range(temp_before):
        steps.extend((DeltaEvent(f"setup{i}"), MarkEvent(f"setup{i}", f"setup{i}", False)))
    steps.extend((DeltaEvent("activation"), MarkEvent("activation", "activation", True)))
    for i in range(temp_after):
        steps.extend((DeltaEvent(f"working{i}"), MarkEvent(f"working{i}", f"working{i}", False)))
    steps.append(MarkEvent("geometry", "geometry", True))
    operations = (Update.ADVANCE,) * advance_before + (Update.ATTACH_BODY, Update.TESSELLATE)
    operations += (Update.ADVANCE,) * advance_after + (Update.ADVANCE_BODY,) * post_attach
    return Session(first_tag, first_delta, tuple(steps), operations, seconds, fraction)


def chain(at, nodes, key, previous_key=None):
    visited = []
    previous = 0
    while at:
        assert at not in visited
        item = nodes[at]
        if previous_key:
            assert item.fields[previous_key] == previous
        visited.append(at)
        previous, at = at, item.fields[key]
    return tuple(visited)


def verify_links(partition):
    nodes = {node.index: node for node in partition.nodes}
    world = nodes[1].fields
    traversal = [1]
    seen = set()
    while traversal:
        at = traversal.pop()
        if at not in seen:
            seen.add(at)
            traversal.extend(references(nodes[at]))
    assert seen == nodes.keys()
    body_at = world["body"]
    body = nodes[body_at].fields
    all_ids = [n.fields["node_id"] for n in nodes.values() if "node_id" in n.fields]
    assert min(all_ids) == body["lowest_node_id"] == 0
    assert sorted(all_ids) == list(range(body["highest_node_id"] + 1))
    for key, kind, expected in (
        ("edge", 16, 12), ("vertex", 18, 8), ("boundary_point", 29, 8),
        ("boundary_curve", 30, 12), ("boundary_surface", 50, 6),
    ):
        ids = chain(body[key], nodes, "next", "previous")
        assert len(ids) == expected and all(nodes[i].kind == kind for i in ids)
    solid, void = nodes[body["shell"]].fields, nodes[nodes[body["region"]].fields["shell"]].fields
    faces = chain(solid["face"], nodes, "next", "previous")
    assert faces == chain(void["front_face"], nodes, "next_front", "previous_front")
    assert len(faces) == 6
    seen_fins = set()
    for vertex in (node for node in nodes.values() if node.kind == 18):
        ids = set(chain(vertex.fields["halfedge"], nodes, "next_at_vx"))
        assert len(ids) == 3 and {nodes[fin].fields["vertex"] for fin in ids} == {vertex.index}
        assert not (ids & seen_fins)
        seen_fins.update(ids)
    assert len(seen_fins) == 24
    definitions = chain(world["attrib_def"], nodes, "next")
    listing = nodes[body["attribute_chains"]].fields
    block = nodes[listing["list_block"]].fields
    actual_order = tuple(nodes[head].fields["definition"] for head in block["entries"] if head)
    assert definitions == actual_order[::-1]
    return nodes


def assert_face_ids(partition, child, plans, first_unique_id):
    nodes = verify_links(partition)
    feature_id = child.extrusion.feature["f08"]
    timestamp = feature_created_at(child.model_header, child.extrusion.feature)
    face_ids = set()
    caps, sides = set(), set()
    for node in partition.nodes:
        if node.kind != 81:
            continue
        data = node.fields
        definition = nodes[data["definition"]].fields
        if nodes[definition["identifier"]].fields["string"] != "FACE_ID_2001":
            continue
        assert nodes[data["owner"]].kind == 14
        none1, none2, primary, secondary = data["fields"]
        assert none1 == none2 == 0
        type_id, feature, created_at, flags, *role = nodes[primary].fields["values"]
        unique_id, external = nodes[secondary].fields["values"]
        assert (feature, created_at, flags, external) == (feature_id, timestamp, 0, 0)
        if type_id == 40:
            cap, contour = role
            assert contour == 0
            caps.add(cap)
        else:
            assert type_id == 74
            line_id, = role
            sides.add(line_id)
        face_ids.add(unique_id)
    assert caps == {0, 1}
    assert sides == {line["f08"] for line in child.profile.sketch["_line_nodes"]}
    assert face_ids == set(range(first_unique_id, first_unique_id + len(plans.brep.faces)))
    return sorted(face_ids)


def close(a, b):
    return isclose(a, b, rel_tol=1e-12, abs_tol=1e-9)


def fresh_case(name, extents, start, times, density, prior_face_ids, audit):
    child = control(name, extents, start, dimensioned=name == "Offset")
    session = schedule(*times)
    baseline = {name: sha256(contents).hexdigest() for name, contents in child.streams.items()}
    attribute_input = Appearance((47, 128, 229) if density is None else (210, 85, 24), 0.375 if density is None else 0.0, density)
    audit["enabled"] = True
    try:
        plan = plan_rectangle(child, session)
        projection = project_rectangle(child, plan, attribute_input, prior_face_ids)
        emitted = write_payloads(projection.partition)
        data = frame_payloads(emitted)
        decoded = read_partition(data)
        assert decoded == projection.partition and frame_payloads(write_payloads(decoded)) == data
    finally:
        audit["enabled"] = False
    assert audit["opens"] == 0
    assert {name: sha256(contents).hexdigest() for name, contents in child.streams.items()} == baseline
    lo_x, lo_y, hi_x, hi_y, depth = extents
    width, height = hi_x - lo_x, hi_y - lo_y
    measured = native_geometry(decoded, (lo_x, lo_y, 0, hi_x, hi_y, depth))
    assert close(measured["signed_volume_mm3"], prod((width, height, depth)))
    assert close(measured["area_mm2"], 2 * (width * height + width * depth + height * depth))
    assert all(close(x, y) for x, y in zip(measured["center_mm"], ((lo_x + hi_x)/2, (lo_y + hi_y)/2, depth/2), strict=True))
    assert measured["loop_direction"] == [1] * 6
    face_ids = assert_face_ids(decoded, child, plan, prior_face_ids + 1)
    atoms = ownership(decoded)
    assert atoms["body_match_tag"] == plan.archive.atom["f180"] == plan.archive.atom["f1b0"]
    assert atoms["atom_id"] == plan.archive.atom["f140"]
    assert atoms["last_modifying_feature"] == plan.archive.atom["f12c"] == plan.archive.atom["f130"]
    assert atoms["body_stamp"] == plan.tracking.body_fields["ENT_TIME_STAMP_2001"][1]
    assert bool(atoms["attributes_by_owner"].get("BODY.SDL/TYSA_DENSITY")) == (density is not None)
    selected, initial, activation = decoded.history
    assert (selected.mark.fields["id"], activation.mark.fields["id"]) == (plan.archive.feature_mark["f18"], plan.archive.part_mark["f18"])
    assert selected.rollback.previous_world.fields["alive"] == 1 and activation.rollback.previous_world.fields["alive"] == 0
    active_deletions = len(selected.rollback.deleted)
    pointer_arrays = len(projection.transient_pointer_allocations)
    assert selected.mark.fields["n_new_nodes"] == active_deletions + pointer_arrays
    assert not initial.rollback and not activation.rollback.deleted
    try:
        projection.require_archive_attachment()
    except IncompletePartition as pending:
        reason = str(pending)
    else:
        raise AssertionError("unproven archive gate admitted")
    return {
        "analytic_geometry": measured,
        "record_counts": dict(sorted(Counter(SCHEMAS[node.kind].name for node in decoded.nodes).items())),
        "face_ids": face_ids,
        "frame_bytes": len(data),
        "framed_sha256": sha256(data).hexdigest(),
        "payload_sha256": [sha256(part).hexdigest() for part in emitted],
        "exact_wire_readback": True,
        "construction_and_codec_file_opens": audit["opens"],
        "geometry_rollback": {"deletions": active_deletions, "untransmitted_pointer_arrays": pointer_arrays,
                              "new_node_count": selected.mark.fields["n_new_nodes"]},
        "archive_attachment_pending": reason,
    }


def disclosed_checks():
    base = Path("re/solidworks/v2026/corpus")
    groups = {
        "ladder": ("L1_boss", "P0_plain", "C1a_control", "C1b_control"),
        "assembly-synchronized": ("A13SyncedSingleChild", "A14SyncedRepeatChild"),
    }
    receipts = {}
    for group, names in groups.items():
        for name in names:
            path = base / group / (name + ".SLDPRT")
            data = path.read_bytes()
            archive = SldprtArchive.from_bytes(data, path)
            partition = read_partition(archive.require("Contents/Config-0-Partition"))
            nodes = {node.index: node for node in partition.nodes}
            world = nodes[1].fields
            ids = chain(world["attrib_def"], nodes, "next")
            declarations = {node.index: node.fields for node in nodes.values() if node.kind == 80}
            assert set(ids) == declarations.keys()
            for index, fields in declarations.items():
                label = nodes[fields["identifier"]].fields["string"]
                predicted = RECTANGLE_DEFINITION_BY_NAME[label].nodes(0)[0].fields
                assert all(predicted[k] == value for k, value in fields.items() if k not in ("identifier", "next"))
            body, = (node.fields for node in nodes.values() if node.kind == 12)
            listing = nodes[body["attribute_chains"]].fields
            block = nodes[listing["list_block"]].fields
            assert ids == tuple(nodes[key].fields["definition"] for key in block["entries"] if key)[::-1]
            assert body["res_size"] == body["res_linear"] / 1e-11
            pointer_arrays = sum(
                code == 9 and node.fields["fields"][index] == 0
                for node in nodes.values() if node.kind == 81
                for index, code in enumerate(declarations[node.fields["definition"]]["fields"])
            )
            selected = partition.history[0]
            deleted = len(selected.rollback.deleted)
            assert selected.mark.fields["n_new_nodes"] - deleted == pointer_arrays
            receipts[name] = {
                "source_sha256": sha256(data).hexdigest(),
                "matched_definitions": len(declarations),
                "reverse_definition_list_equal": True,
                "geometry_rollback_deletions": deleted,
                "geometry_mark_new_nodes": selected.mark.fields["n_new_nodes"],
                "nontransmitted_pointer_arrays": pointer_arrays,
            }
    return receipts


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", action="store_true")
    args = parser.parse_args()
    audit = {"enabled": False, "opens": 0}

    def reject_file_access(event, arguments):
        if audit["enabled"] and event == "open":
            audit["opens"] += 1
            raise RuntimeError("fresh partition construction opened a file")

    addaudithook(reject_file_access)
    cases = (
        ("Offset", (3.125, -11.5, 34.875, 6.75, 13.125), (0, 1, 2, 3),
         (451, 26, 3, 4, 3, 4, 0, 1816661234, 5867491), None, 0),
        ("RotatedStart", (-82.75, 17.875, -61.0, 47.25, 28.25), (1, 2, 3, 0),
         (0xfdf2, 142, 0, 1, 7, 1, 2, 1817000901, 1236789), 1.0, 12),
    )
    fresh = {case[0]: fresh_case(*case, audit) for case in cases}
    result = {"fresh": fresh}
    if args.disclosed:
        result["disclosed_checks"] = disclosed_checks()
    print(dumps(result, indent=2, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
