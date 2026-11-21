import argparse
from dataclasses import replace
from hashlib import sha256
from math import isclose
from pathlib import Path
import codecs
import json
import os
import subprocess
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints, read_cylinder_roles
from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from para.concentric.CheckConcentricAssembly import read_child, verify_emission
from para.concentric.ConcentricAssembly import principal_planes
from para.concentric.ConcentricMate import make_concentric
from para.concentric.PrepareConcentricPersistence import derive_session
from para.concentric.ProjectConcentricRadialIntent import child_intent, radial_from_archive
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, checked, json_digest, require, source_case
from para.cylinder.CylinderAttachment import attach_cylinder_mut


BASELINE = "163309ad92afaff6eeeb7ba434fed8e3ce0dd6b8"
LOCK_SHA256 = "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"
FACE_SHA256 = "897147f4a84c27049138a7e65e5eed0c427c203f61f9c680702492a5494c3915"
FIXTURES = ("ConcentricFeatureNeutral01.json", "ConcentricBrepNeutral01.json")
EPOCH = 1816309903
MATE_STREAM = "Contents/Config-0-MatesList"


def fingerprint(payload):
    return sha256(payload).hexdigest()


def source_inventory(root):
    files = tuple(path for directory in ("src", "re/tooling/sw2026")
                  for path in (root / directory).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)
    files += tuple(root / "re/solidworks/inputs" / item for item in FIXTURES)
    return {path.relative_to(root).as_posix(): fingerprint(path.read_bytes()) for path in files}


def inventory_receipt(values):
    return {"paths": len(values), "sha256": fingerprint(json.dumps(values, sort_keys=True).encode())}


def neutral_d01(seed, parent, checked_axes, source_shape, label):
    child, _ = child_intent(source_shape.child, *radial_from_archive(source_shape.native.LinkValue))
    child_name = "D01SignedChild"
    child = replace(child, metadata={"name": child_name})
    graph = seed.assembly
    source = parent.assembly
    old_occurrences = sorted(source.instances, key=lambda value: value.order)
    root_id = graph.root_definition_id
    definitions = tuple(replace(row, name=label if row.id == root_id else child_name) for row in graph.definitions)
    instances = tuple(replace(row, name=f"{child_name}-{original.reference_number}", transform=original.transform,
                              reference_number=original.reference_number, fixed=original.fixed)
                      for row, original in zip(graph.instances, old_occurrences, strict=True))
    translated = {original.id: target.id for original, target in zip(old_occurrences, instances, strict=True)}
    entities = tuple(replace(row, instance_path=(translated[checked["occurrence"]],), radius=source_shape.radius)
                     for row, checked in zip(graph.mate_entities, checked_axes, strict=True))
    source_mate, = source.mates
    mate = replace(graph.mates[0], name=source_mate.name, alignment=source_mate.alignment,
                   attributes={"rotation_locked": source_mate.attributes["rotation_locked"]})
    result = replace(seed, metadata={"name": label}, assembly=replace(graph, definitions=definitions,
                     instances=instances, documents=(replace(graph.documents[0], document=child),),
                     mates=(mate,), mate_entities=entities))
    result.AssertValid()
    return result


def plan_bundle(document, written_at):
    model = ReadAsmModel(document)
    destination = "C:\\KitSignedConcentric\\" + model.RootValue.name + ".SLDASM"
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, written_at)
    child = model.ChildDocument
    plain = replace(child, brep=None)
    plan = ProjectCircle(plain)
    recipe = MakePartRecipe(plan, written_at)
    settings = BindPartIntent(plain, plan, recipe, SelfFileInput(paths.ChildValue.PathName, written_at))
    session, edits = derive_session(plain, written_at)
    driver = "diameter" if plan.IsDiameter else "radius"
    attachment = attach_cylinder_mut(MakeCirclePart(plain, settings), session, edits, 0,
                                     tessellated_faces=True, driver_mode=driver)
    nodes = {item.index: XmtNode(item.index, item.kind, item.fields) for item in attachment.projection.partition.nodes}
    profile = "derived_feature" if child.brep is None else "authored_brep"
    binding = bind_cylinder(child, attachment.candidate, nodes, profile=profile, driver_mode=driver)
    intent = project_concentric(document, {model.ChildValue.id: binding})
    metadata = MakeAsmRecipe(model, recipe, principal_planes(document, written_at), paths.ParentValue)
    placements = tuple(ReadAsmPlace(row) for row in model.Occurrences)
    return attachment, intent, metadata, placements


def emit_parts(bundle, axes=None, *, wrong_alignment=False, stale_pose=False, repeated_occurrence=False):
    attachment, intent, metadata, placements = bundle
    state = MakeAsmBase(metadata)
    headers = MakeAsmHeaders(state, metadata)
    references = PutPartRefsMut(state, attachment.candidate, metadata, placements, headers)
    selected = tuple(row.occurrence_index for row in intent.ends)
    ordered = tuple(references[index] for index in selected)
    poses = tuple(row.placement.FrameValue for row in intent.ends)
    alignment = intent.alignment_code
    if wrong_alignment:
        alignment = 3 - alignment
    if stale_pose:
        poses = (replace(poses[0], OriginValue=(0.0, 0.0, 0.0)), poses[1])
    if repeated_occurrence:
        ordered = (ordered[0], ordered[0])
    mate = make_concentric(state, metadata, headers, ordered, poses, attachment,
                           intent.mate.name, alignment, intent.rotation_locked,
                           selected.index(intent.fixed_index), endpoint_axes=axes)
    streams = EmitAsmStreams(state, attachment.candidate, metadata, headers, references, (mate,)).StreamsValue
    return BuildSldprt(streams, FormatVersion=4)


def verify_parts(payload, bundle, axes=None):
    attachment, intent, _, _ = bundle
    names = tuple(row.occurrence.name for row in intent.ends)
    return verify_emission(payload, attachment, intent.alignment_code, intent.rotation_locked,
                           intent.fixed_index, names, expected_local_axes=axes)


def controlled_archive_change(payload, update):
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    mates = ReadMatesMut(archive.require(MATE_STREAM), link.ResolvedValue)
    update(mates.RootsValue[0].FieldsValue)
    mutated = WriteMatesMut(mates.RootsValue, link.ResolvedValue)[0]
    require(mutated != archive.require(MATE_STREAM), "diagnostic did not change the generated stream")
    return BuildSldprt(dict(archive.streams) | {MATE_STREAM: mutated}, FormatVersion=archive.format_version)


def reject_calls(unsigned, candidate, bundle, axes):
    neg, pos = axes[0], tuple(-value for value in axes[0])

    def wrong_local(fields):
        fields["f410"][0]["o"].FieldsValue["f108"] = dict(zip("xyz", pos, strict=True))

    def wrong_extent(fields):
        active = fields["f410"][0]["o"].FieldsValue
        active["fb8"] = -active["fb8"]

    def wrong_snapshot(fields):
        support = fields["f3c8"][0]["o"].FieldsValue
        support["fe8"] = {key: -value for key, value in support["fe8"].items()}

    def wrong_order(fields):
        fields["f410"] = list(reversed(fields["f410"]))

    cases = {
        "axis_count": lambda: emit_parts(bundle, (neg,)),
        "zero_axis": lambda: emit_parts(bundle, ((0.0, 0.0, 0.0), neg)),
        "nonunit_axis": lambda: emit_parts(bundle, ((0.0, 0.0, 2.0), neg)),
        "nonfinite_axis": lambda: emit_parts(bundle, ((0.0, 0.0, float("nan")), neg)),
        "boolean_scalar": lambda: emit_parts(bundle, ((False, 0.0, -1.0), neg)),
        "foreign_axis": lambda: emit_parts(bundle, ((1.0, 0.0, 0.0), neg)),
        "mixed_local_signs": lambda: emit_parts(bundle, (neg, pos)),
        "wrong_alignment": lambda: emit_parts(bundle, axes, wrong_alignment=True),
        "stale_occurrence_pose": lambda: emit_parts(bundle, axes, stale_pose=True),
        "duplicate_occurrence": lambda: emit_parts(bundle, axes, repeated_occurrence=True),
        "unexpected_local_sign": lambda: verify_parts(unsigned, bundle, axes),
        "wrong_emitted_local": lambda: verify_parts(controlled_archive_change(candidate, wrong_local), bundle, axes),
        "wrong_emitted_extent": lambda: verify_parts(controlled_archive_change(candidate, wrong_extent), bundle, axes),
        "wrong_emitted_support_axis": lambda: verify_parts(controlled_archive_change(candidate, wrong_snapshot), bundle, axes),
        "wrong_emitted_order": lambda: verify_parts(controlled_archive_change(candidate, wrong_order), bundle, axes),
    }
    rejected = {}
    for name, operation in cases.items():
        try:
            operation()
        except (ValueError, AssertionError) as error:
            rejected[name] = str(error) or type(error).__name__
        else:
            raise ValueError("signed research writer accepted " + name)
    return rejected


def guarded(document, axes, written_at, *, mutations=False):
    GetDocumentCaps(ReadAsmModel(document).ChildDocument)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    active = True
    denied = []

    def audit(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            denied.append(event)
            raise RuntimeError("signed constructor attempted runtime access: " + event)

    sys.addaudithook(audit)
    try:
        bundle = plan_bundle(document, written_at)
        signed = emit_parts(bundle, axes)
        repeat_bundle = plan_bundle(document, written_at)
        repeat = emit_parts(repeat_bundle, axes)
        assert signed == repeat and bundle[0].file_bytes == repeat_bundle[0].file_bytes
        unsigned = emit_parts(bundle)
        actual = verify_parts(signed, bundle, axes)
        positive = verify_parts(unsigned, bundle)
        unsigned_streams = SldprtArchive.from_bytes(unsigned).streams
        signed_streams = SldprtArchive.from_bytes(signed).streams
        assert set(unsigned_streams) == set(signed_streams)
        assert {name for name in signed_streams if signed_streams[name] != unsigned_streams[name]} == {MATE_STREAM}
        rejected = reject_calls(unsigned, signed, bundle, axes) if mutations else {}
    finally:
        active = False
    require(not denied, "signed writer or verifier used runtime file, process or network")
    return bundle[0], signed, {
        "signed": actual, "implicit": positive, "child_bytes": len(bundle[0].file_bytes),
        "signed_parent_sha256": fingerprint(signed), "legacy_parent_sha256": fingerprint(unsigned),
        "signed_parent_bytes": len(signed), "legacy_parent_bytes": len(unsigned),
        "changed_streams": [MATE_STREAM], "runtime_io_attempts": len(denied),
        "same_process_repeated_pair_bytes_exact": True, "rejected": rejected,
    }


def legacy_pair(closure, fixture, variant, output):
    toolkit = closure / "re/tooling/sw2026"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=os.pathsep.join(map(str, (closure / "src", toolkit, toolkit / "serial"))))
    request = closure / "re/solidworks/inputs" / fixture
    command = (sys.executable, str(toolkit / "para/concentric/CheckConcentricAssembly.py"),
               str(request), "--case", str(variant), "--output", str(output))
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=90, check=True)
    receipt = json.loads(result.stdout)
    return receipt, {path.name: path.read_bytes() for path in output.iterdir()}


def verify_legacy(before, out):
    reports = []
    for ordinal, fixture in enumerate(FIXTURES, 1):
        former, before_files = legacy_pair(before, fixture, ordinal, out / f"LegacyBefore{ordinal}")
        current, after_files = legacy_pair(REPO, fixture, ordinal, out / f"LegacyAfter{ordinal}")
        assert current == former and before_files == after_files and current["runtime_io_attempts"] == 0
        reports.append({"fixture": fixture, "input_sha256": current["input_sha256"],
                        "alignment": current["alignment"], "locked": current["rotation_locked"],
                        "ordered_occurrences": current["occurrence_names"],
                        "same_receipt_and_archive_bytes": True,
                        "full_archive_sha256": {name: fingerprint(payload) for name, payload in after_files.items()}})
    return reports


def compare_source_selection(actual, expected):
    for ordinal, row in enumerate(expected):
        signed = actual["signed"]
        assert signed["local_axes"][ordinal] == row["local_axis"]
        assert all(isclose(left, right, rel_tol=1e-12, abs_tol=1e-12) for left, right in
                   zip(signed["world_axes"][ordinal], row["world_axis"], strict=True))
        assert all(isclose(left, right, rel_tol=1e-12, abs_tol=1e-12) for left, right in
                   zip(signed["world_origins"][ordinal], row["generated_world_origin_m"], strict=True))
        assert all(isclose(left, right, rel_tol=1e-12, abs_tol=1e-12) for left, right in
                   zip(signed["active_intervals"][ordinal], row["generated_axial_bounds_m"], strict=True))


def main():
    parser = argparse.ArgumentParser(description="Measure signed concentric writer fields on the disclosed D01 inputs")
    parser.add_argument("disclosed_receipt_directory", type=Path)
    parser.add_argument("baseline_closure", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir()
    before = args.baseline_closure.resolve()
    inventory = {label: source_inventory(root) for label, root in (("before", before), ("after", REPO))}
    scopes = set(inventory["before"]) | set(inventory["after"])
    deltas = {path for path in scopes if inventory["before"].get(path) != inventory["after"].get(path)}
    changed_tools = ("ConcentricMate.py", "CheckConcentricAssembly.py", Path(__file__).name)
    require(deltas == {"re/tooling/sw2026/para/concentric/" + name for name in changed_tools},
            "comparison closures contain additional missing or changed paths")
    previous = checked(REPO / "re/solidworks/measurements/2026/ConcentricSourceFaceCorrespondence01.json", FACE_SHA256)
    require(json.loads(previous)["passed"], "the pinned source correspondence did not pass")
    inputs = REPO / "re/solidworks/inputs"
    authored = [FromData(json.loads((inputs / name).read_bytes())) for name in FIXTURES]
    d01 = args.disclosed_receipt_directory / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(d01 / "lock.json", LOCK_SHA256))
    require(lock["source_locked"] and not lock["heldout_source_locked"], "only the disclosed source lock may be read")
    reports = {}
    for ordinal, (phase, digests) in enumerate(D01_LOCKED.items()):
        native = d01 / "Native" / phase
        file_names = ("ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT")
        parent, parent_bytes, source = source_case(native, *file_names, digests)
        original_parent, original_child = json_digest(parent), json_digest(source.child)
        axes_owner = map_source_endpoints(parent, parent_bytes, source, source)
        axes = tuple(row["local_axis"] for row in axes_owner)
        label = "D01SignedWrapper" + phase
        clean = neutral_d01(authored[0], parent, axes_owner, source, label)
        attachment, _, observation = guarded(clean, axes, EPOCH + ordinal, mutations=not ordinal)
        target = open_document(attachment.file_bytes, source_format="solidworks.sldprt",
                               strict=True, include_tessellation=False)
        roles = read_cylinder_roles(target, read_child(attachment))
        mapped = map_source_endpoints(parent, parent_bytes, source, roles)
        compare_source_selection(observation, mapped)
        require(json_digest(parent) == original_parent and json_digest(source.child) == original_child,
                "the original immutable source changed")
        require(tuple(fingerprint(checked(native / file, digest)) for file, digest in zip(file_names, digests, strict=True))
                == digests, "the immutable input pair changed")
        reports[phase] = {"parent_source_sha256": digests[0], "child_source_sha256": digests[1],
                          "scoped_neutral_request_sha256": json_digest(clean), "endpoint_correspondence": mapped,
                          "emission": observation}
    synthetic_axes = ((0.0, 0.0, -1.0),) * 2
    _, _, synthetic = guarded(authored[1], synthetic_axes, EPOCH + 2)
    assert synthetic["signed"]["alignment"] == 2 and synthetic["signed"]["rotation_locked"] is True
    assert any(abs(axis[0]) > 0.01 for axis in synthetic["signed"]["world_axes"])
    unsigned_order = synthetic["implicit"]["occurrence_names"]
    assert synthetic["signed"]["occurrence_names"] == unsigned_order and tuple(row[-1] for row in unsigned_order) == ("2", "1")
    legacy = verify_legacy(before, output)
    assert source_inventory(before) == inventory["before"] and source_inventory(REPO) == inventory["after"]
    result = {
        "schema": "kit.sw2026.signed-concentric-wrapper-construction.v1", "comparison_base": BASELINE,
        "prior_face_receipt_sha256": FACE_SHA256, "d01_lock_sha256": LOCK_SHA256,
        "source_tool_sha256": {
            name: fingerprint((Path(__file__).parent / name).read_bytes())
            for name in changed_tools
        },
        "source_closures": {label: inventory_receipt(value) for label, value in inventory.items()},
        "legacy": legacy, "disclosed": reports, "authored_offset_axis_anti_aligned_locked": synthetic,
        "native_processes": 0, "sealed_inputs_read": 0, "whole_source_admitted": False,
        "public_writer_enabled": False, "passed": True,
    }
    with (output / "ConcentricSignedWrapperConstruction01.json").open("x", encoding="utf-8") as file:
        json.dump(result, file, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
    print(fingerprint((output / "ConcentricSignedWrapperConstruction01.json").read_bytes()))


if __name__ == "__main__":
    main()
