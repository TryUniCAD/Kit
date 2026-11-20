import argparse
from dataclasses import asdict, replace
from hashlib import sha256
import codecs
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints, match_cylinder_shapes, read_cylinder_roles, wire_index
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylChild import ReadCylChild
from interchange.serialization.EncodeData import ToData
from para.concentric.PrepareConcentricPersistence import derive_session
from para.concentric.ProjectConcentricRadialIntent import child_intent, radial_from_archive
from para.cylinder.CylinderAttachment import attach_cylinder_mut


BASELINE = "c4a54e48504f7bfaed0c14e3aaac9996e42bda10"
D01_LOCK = "D01"
D01_LOCKED = {
    "Source": ("2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2",
               "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"),
    "Edited": ("34c3229540d81f87a6af51acdc8194c7a45a25e1cf72eafaadbdbbfa5dd26c52",
               "d566026624218f75de64dcee1e8a10890c7359df7abbe2535cb051a572524c93"),
}
RADIAL_LOCKED = {
    "Frozen": ("9474ca54466a450eec3ba5e49703053fe160e0a221647b2bcc984d8d3672dc74",
               "699be1addf4b644f1ebdeecc6862f65610155d294e10fa6d7cbcf3d6a224f1cd"),
    "Working": ("19d1b44bff684f0414549b5d997fba89f9e67368e20aac31d855c947e0e3a5a3",
                "d39693d2617c0900a607fb7e6e5be041b7caea906ebcd0cecc69fb8d767a7416"),
}


def require(value, why):
    if not value:
        raise ValueError(why)


def checked(path, digest):
    require(path.is_file() and not path.is_symlink(), "input is not the expected regular disclosed artifact")
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == digest, "disclosed input SHA-256 differs: " + path.name)
    return payload


def json_digest(document):
    return sha256(json.dumps(ToData(document), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_case(directory, parent_name, child_name, digests):
    parent_path, child_path = directory / parent_name, directory / child_name
    parent_hash, child_hash = digests
    parent_bytes = checked(parent_path, parent_hash)
    _ = checked(child_path, child_hash)
    parent = open_document(parent_path, strict=True, include_brep=True, include_tessellation=False)
    child = parent.assembly.documents[0].document
    require(parent.source.sha256 == parent_hash and child.source.sha256 == child_hash,
            "public reader did not resolve the locked parent and child")
    child_owner = ReadCylChild(child_path, child, "Default")
    return parent, parent_bytes, read_cylinder_roles(child, child_owner)


def guarded_child(shape, case, written_at, out):
    root = shape.child
    native_circle = radial_from_archive(shape.native.LinkValue)
    document, source_drivers = child_intent(root, *native_circle)
    name = "D01FaceRole" + case
    document = replace(document, metadata={"name": name})
    plan = ProjectCircle(document)
    recipe = MakePartRecipe(plan, written_at)
    destination = SelfFileInput("C:\\KitD01FaceRole\\" + name + ".SLDPRT", written_at)
    bound = BindPartIntent(document, plan, recipe, destination)
    session, updates = derive_session(document, written_at)
    GetDocumentCaps(document)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    active = True
    denied = []

    def audit(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            denied.append(event)
            raise RuntimeError("unexpected construction access: " + event)

    sys.addaudithook(audit)
    try:
        repeated = tuple(attach_cylinder_mut(MakeCirclePart(document, bound), session, updates, 0,
                                           tessellated_faces=True, driver_mode="radius").file_bytes for _ in range(2))
    finally:
        active = False
    require(not denied and repeated[0] == repeated[1], "guarded fresh cylinder bytes are nondeterministic")
    payload = repeated[0]
    path = out / (name + ".SLDPRT")
    with path.open("xb") as handle:
        handle.write(payload)
    generated = open_document(path, strict=True, include_brep=True, include_tessellation=False)
    native = ReadCylChild(path, generated, "Default")
    roles = read_cylinder_roles(generated, native)
    return roles, {"source_driving_owners": source_drivers, "neutral_request_sha256": json_digest(document),
                   "generated_sha256": sha256(payload).hexdigest(), "generated_bytes": len(payload),
                   "independent_builds": len(repeated), "writer_runtime_file_process_or_network_attempts": len(denied)}


def roles_data(value):
    return {
        "child_sha256": value.native.SourceHash, "lateral_face": value.side_face,
        "lateral_node_id": value.native.FaceValue.Integer("node_id"), "body_atom": value.native.AtomValue,
        "carrier_origin_mm": value.carrier_origin, "carrier_sign": value.carrier_sign,
        "producer": value.producer, "permanent_arc_marker": value.native.ArcMarker,
        "radius_mm": value.radius, "start_end_centers_mm": value.centers,
        "rims": {str(role): asdict(rim) for role, rim in value.rims.items()},
    }


def change_public_row(source, field, identity, **updates):
    model = source.child.brep
    changes = tuple(replace(row, **updates) if row.id == identity else row for row in getattr(model, field))
    return replace(source.child, brep=replace(model, **{field: changes}))


def reject_cases(parent, parent_bytes, source, target, wrong_size, expected_edited):
    body = source.child.brep
    lateral, = (row for row in body.faces if row.id == source.side_face)
    carrier, = (row for row in body.surfaces if row.id == lateral.surface_id)
    cap, = (row for row in body.faces if row.id == source.rims[0].cap_face)
    cap_plane, = (row for row in body.surfaces if row.id == cap.surface_id)
    ring, = (row for row in body.curves if row.id == source.rims[0].curve)
    seam, = (row for row in body.vertices if row.id == source.rims[0].seam)
    mate_rows = parent.assembly.mate_entities
    native_nodes = dict(source.native.NodesValue)
    cap_node = native_nodes[wire_index(cap.id)]
    words_index = ReadCylAttr(native_nodes, cap_node, "FACE_ID_2001").Indexes("fields")[2]
    actual_words = native_nodes[words_index]
    selector = actual_words.Indexes("values")
    native_nodes[words_index] = replace(actual_words, FieldsValue={**actual_words.FieldsValue,
                                                                  "values": (*selector[:4], 1 - selector[4], selector[5])})
    wrong_selection = replace(mate_rows[0], source_entity_id=cap.id)
    wrong_occurrence = replace(mate_rows[0], instance_path=mate_rows[1].instance_path)
    occurrence = next(row for row in parent.assembly.instances if row.id == mate_rows[0].instance_path[0])
    displaced = list(occurrence.transform.values)
    displaced[11] += 0.5
    displaced = replace(occurrence, transform=replace(occurrence.transform, values=tuple(displaced)))
    shifted_children = tuple(displaced if row is occurrence else row for row in parent.assembly.instances)
    reversed_axes = tuple(replace(row, attributes={**row.attributes, "stored_axis": tuple(-axis for axis in row.attributes["stored_axis"])})
                          for row in mate_rows)
    closed, = (row for row in body.edges if row.id == source.rims[0].edge)
    cases = {
        "wrong_lateral_point": lambda: read_cylinder_roles(
            change_public_row(source, "surfaces", carrier.id, origin=replace(carrier.origin, x=carrier.origin.x + 0.5)),
            source.native),
        "axially_shifted_carrier_origin": lambda: read_cylinder_roles(
            change_public_row(source, "surfaces", carrier.id, origin=replace(carrier.origin, z=carrier.origin.z + 0.5)),
            source.native),
        "wrong_cap_point": lambda: read_cylinder_roles(
            change_public_row(source, "surfaces", cap_plane.id, origin=replace(cap_plane.origin, z=cap_plane.origin.z + 0.5)),
            source.native),
        "wrong_rim_center": lambda: read_cylinder_roles(
            change_public_row(source, "curves", ring.id, center=replace(ring.center, y=ring.center.y + 0.5)),
            source.native),
        "wrong_seam_point": lambda: read_cylinder_roles(
            change_public_row(source, "vertices", seam.id, point=replace(seam.point, x=seam.point.x + 0.5)),
            source.native),
        "incomplete_closed_edge": lambda: read_cylinder_roles(
            change_public_row(source, "edges", closed.id, end_parameter=closed.end_parameter - 0.2),
            source.native),
        "extra_lateral_loop": lambda: read_cylinder_roles(
            change_public_row(source, "faces", lateral.id, loop_ids=lateral.loop_ids + (cap.loop_ids[0],)),
            source.native),
        "reversed_native_cap_role": lambda: read_cylinder_roles(
            source.child, replace(source.native, NodesValue=native_nodes)),
        "cap_substituted_as_lateral_selection": lambda: map_source_endpoints(
            replace(parent, assembly=replace(parent.assembly, mate_entities=(wrong_selection, mate_rows[1]))),
            parent_bytes, source, target),
        "same_occurrence_twice": lambda: map_source_endpoints(
            replace(parent, assembly=replace(parent.assembly, mate_entities=(wrong_occurrence, mate_rows[1]))),
            parent_bytes, source, target),
        "occurrence_shift_along_same_carrier": lambda: map_source_endpoints(
            replace(parent, assembly=replace(parent.assembly, instances=shifted_children)),
            parent_bytes, source, target),
        "both_wrapper_signs_reversed": lambda: map_source_endpoints(
            replace(parent, assembly=replace(parent.assembly, mate_entities=reversed_axes)),
            parent_bytes, source, target),
        "coaxial_but_different_extent": lambda: match_cylinder_shapes(source, wrong_size),
        "different_actual_parent_archive": lambda: map_source_endpoints(parent, expected_edited, source, target),
        "whole_source_still_outside_ordinary_assembly_writer": lambda: ReadAsmModel(parent),
    }
    results = {}
    for name, operation in cases.items():
        try:
            operation()
        except ValueError as error:
            results[name] = str(error)
        else:
            raise ValueError("unexpectedly admitted " + name)
    return results


def main():
    parser = argparse.ArgumentParser(description="Compare only the pinned disclosed D01 and radial face owners in fresh offline target graphs")
    parser.add_argument("oracle_receipt_directory", type=Path)
    parser.add_argument("scratch_output", type=Path)
    args = parser.parse_args()
    evidence = args.oracle_receipt_directory.resolve()
    output = args.scratch_output.resolve()
    output.mkdir()
    d01 = evidence / "ConcentricMateSourcePacket02/Disclosed" / D01_LOCK
    lock_payload = (d01 / "lock.json").read_bytes()
    lock = json.loads(lock_payload)
    require(lock["source_locked"] and not lock["heldout_source_locked"], "only the disclosed D01 source lock is permitted")
    author_payload = (d01 / "author.json").read_bytes()
    author = json.loads(author_payload)
    require(author["passed"] and author["result"]["passed"], "the disclosed D01 author witness failed")
    radial = evidence / "RadialConcentric01"
    native_receipt = checked(radial / "Result.json", "3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03")
    measured = json.loads(native_receipt)
    require(measured["passed"] and measured["phases"]["Reopen"]["passed"], "the disclosed radial persistence witness failed")

    cases, artifacts, reports = {}, [], {}
    for phase, digests in D01_LOCKED.items():
        locked = lock["native_artifacts"][phase.lower()]
        require(tuple(locked[role]["sha256"] for role in ("parent", "child")) == digests, "D01 manifest hashes changed")
        folder = d01 / "Native" / phase
        files = ("ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT")
        cases[phase] = source_case(folder, *files, digests)
        artifacts.extend((folder / name, digest) for name, digest in zip(files, digests, strict=True))
    for phase, digests in RADIAL_LOCKED.items():
        folder = radial / phase
        files = ("RadialConcentricProbe.SLDASM", "DisclosedRadialSceneProbe.SLDPRT")
        cases[phase] = source_case(folder, *files, digests)
        artifacts.extend((folder / name, digest) for name, digest in zip(files, digests, strict=True))
    fingerprints = {phase: (json_digest(value[0]), json_digest(value[2].child)) for phase, value in cases.items()}
    for index, phase in enumerate(("Source", "Edited", "Working")):
        parent, parent_bytes, source = cases[phase]
        target, guarded = guarded_child(source, phase, 1816308507 + index, output)
        endpoints = map_source_endpoints(parent, parent_bytes, source, target)
        reports[phase] = {"parent_sha256": parent.source.sha256, "source": roles_data(source),
                          "target": roles_data(target), "face_ids": match_cylinder_shapes(source, target),
                          "endpoints": endpoints, "generation": guarded}
        if phase == "Source":
            native_frozen = cases["Frozen"][2]
            reports[phase]["pinned_generated_target"] = {
                "body": roles_data(native_frozen), "parent_sha256": cases["Frozen"][0].source.sha256,
                "faces": match_cylinder_shapes(source, native_frozen),
                "endpoints": map_source_endpoints(parent, parent_bytes, source, native_frozen),
            }
            original, original_bytes, original_source, original_target = parent, parent_bytes, source, target
        if phase == "Edited":
            different_extent = target
    rejected = reject_cases(original, original_bytes, original_source, original_target, different_extent, cases["Edited"][1])
    require(all(fingerprints[phase] == (json_digest(row[0]), json_digest(row[2].child)) for phase, row in cases.items()),
            "the source ownership or presentation changed during the correspondence")
    for path, digest in artifacts:
        checked(path, digest)
    result = {"schema": "kit.sw2026.disclosed-concentric-face-correspondence.v1",
              "passed": True, "comparison_base": BASELINE,
              "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "correspondence_sha256": sha256((SW2026 / "CheckConcentricSourceBrep.py").read_bytes()).hexdigest(),
              "d01_lock_sha256": sha256(lock_payload).hexdigest(), "d01_author_sha256": sha256(author_payload).hexdigest(),
              "radial_author_sha256": sha256(native_receipt).hexdigest(),
              "reports": reports, "rejected": rejected, "source_bytes_and_models_unchanged": True,
              "new_native_processes": 0, "sealed_inputs_read": 0, "whole_source_admitted": False}
    receipt = output / "ConcentricSourceFaceCorrespondence01.json"
    with receipt.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(sha256(receipt.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
