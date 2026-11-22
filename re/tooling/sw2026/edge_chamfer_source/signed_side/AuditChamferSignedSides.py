from argparse import ArgumentParser
from dataclasses import replace
from pathlib import Path
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
STUDY = ROOT / "re/tooling/sw2026"
sys.path[:0] = [str(path) for path in (ROOT, ROOT / "src", STUDY, STUDY / "serial",
                                      HERE.parent.parent, STUDY / "materials")]

from AuditTypedChamfer import (
    NAMES, checked, checked_json, digest, expected_inputs, guard_runtime, inspect, registry, require,
)
from ChamferModel import validate_spec
from FilletPacket import BUILD, CONTROL, ORACLE
from MaterialPe import PeImage

MODEL_SHA = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
PART_SHA = "aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9"
CD_NAMES = ("ChamferComplementAxialC", "ChamferPrincipalTopD")
CD_LOCK = "2bce5961120ea7d8ea95ceaa5c10f7cbdbe6338152833357304647f432b86ff8"
CD_JOB = "f68069989276d1db1204e52b2b84075698921c25849da0eb6eeb1d9c01520c01"
CD_PHASES = ("author", "reopen-edit-save", "edited-reopen")


def binary_owners(model_path, part_path, objdump):
    model, part = (PeImage(path.resolve(strict=True)) for path in (model_path, part_path))
    require(model.sha256 == MODEL_SHA and part.sha256 == PART_SHA
            and all(not image.path.is_relative_to(ROOT) and image.u16(image.pe + 4) == 0x8664
                    for image in (model, part)), "source images must be the exact licensed installed x64 pair")
    imports = part.imports()
    target = imports[0x1803E3D28]
    getter, = [row for row in model.exports() if row["name"] == target["name"]]
    require(target["module"].casefold() == "sldmodu.dll" and getter["address"] == "0x4b28d730",
            "the per-entity flip accessor resolves to the wrong module or owner")
    roles = []
    for image, name, begin, end, anchors in (
        (model, "component_direction_accessor", 0x4B28D730, 0x4B28D73A,
         {0x4B28D730: "mov eax, dword ptr [rcx + 0x68]", 0x4B28D733: "shr eax, 0x7", 0x4B28D736: "and eax, 0x1"}),
        (model, "component_direction_setter", 0x4B291FE0, 0x4B291FE8,
         {0x4B291FE0: "or dword ptr [rcx + 0x68], 0x80"}),
        (part, "separate_feature_flip_setter", 0x1801711B0, 0x1801711B7,
         {0x1801711B0: "mov dword ptr [rcx + 0x860], edx"}),
        (part, "same_physical_edge_selector", 0x180248637, 0x180248763,
         {0x18024868F: "cmp rbx, r13", 0x180248692: "je 0x180248758",
          0x18024875B: "call qword ptr [rip + 0x19b5c7]"}),
        (part, "base_coedge_operand", 0x180246010, 0x180246036,
         {0x180246010: "mov rcx, qword ptr [rcx + 0x8a8]", 0x18024601E: "call qword ptr [rip + 0x1a1acc]"}),
        (part, "base_coedge_orientation", 0x1802462C3, 0x1802462F0,
         {0x1802462C6: "call qword ptr [rip + 0x1a424c]"}),
    ):
        data = check_output((objdump, "-d", "--no-show-raw-insn", "--x86-asm-syntax=intel",
                             f"--start-address={hex(begin)}", f"--stop-address={hex(end)}", str(image.path)), text=True)
        lines = {line.split(":", 1)[0]: " ".join(line.split(":", 1)[1].split())
                 for line in data.splitlines() if line[:1] in ("1", "4") and ":" in line}
        require(all(lines.get(f"{address:x}", "").startswith(prefix) for address, prefix in anchors.items()),
                "exact installed direction instruction or field binding differs")
        roles.append(image.pin(name, begin, end) | {"module": image.path.name, "image_sha256": image.sha256})
    operand = imports[0x1803E7AF0]
    coedge = imports[0x1803EA518]
    require(operand["name"].startswith("?getCoEdge@moCompEdge_c")
            and coedge["name"].startswith("?sameDirectionAsEdge@gcCoEdge_w"),
            "base coedge lookup and orientation imports differ")
    return {"component_direction_field": "f68", "component_direction_mask": 128,
            "separate_feature_flip_field": "f860", "getter_import_address": "0x1803e3d28",
            "getter_export": getter["name"], "base_coedge_field": "f8a8",
            "base_coedge_import": operand, "orientation_import": coedge, "roles": roles}


def authored_stock(case):
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector

    model = MakePlainDoc(case["name"], *case["size_mm"])
    cx, cy = case["center_mm"]
    sketch, = model.sketches

    def translated(value):
        return PlaneVector(value.x + cx, value.y + cy)

    entities = tuple(replace(item, geometry=LineGeometry(translated(item.geometry.start), translated(item.geometry.end)))
                     for item in sketch.entities)
    return replace(model, sketches=(replace(sketch, entities=entities),))


def support_orders(model, endpoints):
    from ChamferEdgeOwners import same_endpoints
    from para.prism.SdkPrismPartition import design_geometry

    body, surfaces, _, _, _ = design_geometry(model)
    vertices = {point.id: tuple(0.001 * getattr(point.point, axis) for axis in "xyz") for point in body.vertices}
    edge, = (value for value in body.edges if same_endpoints(
        (vertices[value.start_vertex_id], vertices[value.end_vertex_id]), endpoints))
    uses = {use.id: use for use in body.coedges}
    opposites = {use.id: other for use in uses.values() for other in uses.values()
                 if use.id != other.id and use.edge_id == other.edge_id}
    loops = {use: loop for loop in body.loops for use in loop.coedge_ids}
    loop_owners = {loop: face for face in body.faces for loop in face.loop_ids}
    carriers = {surface.id: surface.normal for surface in body.surfaces}
    result = {}
    for use in (value for value in uses.values() if value.edge_id == edge.id):
        loop = loops[use.id]
        index = loop.coedge_ids.index(use.id)
        roles = (use, opposites[use.id], opposites[loop.coedge_ids[index - 1]],
                 opposites[loop.coedge_ids[(index + 1) % len(loop.coedge_ids)]])
        faces = [loop_owners[loops[role.id].id] for role in roles]
        require(len({face.id for face in faces}) == 4 and use.reversed not in result, "ambiguous signed face tuple")
        result[use.reversed] = [{"normal_axis": next(axis for axis in "xyz" if abs(getattr(carriers[face.surface_id], axis)) == 1),
                                 "face_ordinal": surfaces[face.id].number} for face in faces]
    require(set(result) == {False, True}, "ordinary edge requires two actual reciprocal coedges")
    return result


def shape_axes(case):
    from FilletModel import edge_role, stock
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPartFromPlan
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    document = authored_stock(case)
    _, axis, across, start, _ = edge_role(case)
    _, bounds = stock(case)
    plan = ProjectBlind(document, ReadLineLoop)
    model = MakeBlindPartFromPlan(document, MakePartRecipe(plan, 1795485600), plan)
    end = list(start)
    end[axis] = bounds[axis][1]
    orders = support_orders(model, (start, end))
    positive = "xyz".index(orders[False][0]["normal_axis"])
    reciprocal = "xyz".index(orders[True][0]["normal_axis"])
    require({positive, reciprocal} == set(across), "modeled fins do not distinguish both incident carriers")
    return axis, across, positive, orders


def cd_source(folder):
    require(folder.name == "DisclosedNative" and folder.parent.name == "ChamferSignedSideSource01",
            "use only the exact disclosed signed public capture")
    lock = checked_json(folder / "SourceLock.json", CD_LOCK)
    require(lock["passed"] is True and lock["cohort"] == "disclosed" and lock["idle_after"] is True
            and lock["inputs_unchanged"] is True and lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE
            and lock["control_sha256"] == CONTROL and lock["job_sha256"] == CD_JOB
            and lock["fresh_processes"] == lock["distinct_processes"] == 8 and lock["writer_output_count"] == 0
            and lock["heldout_writer_acceptance"] is False, "signed public lock is not a healthy disclosed capture")
    cases = validate_spec(checked_json(HERE.with_name("ChamferSignedSideInputs.json"), lock["spec_sha256"]))
    require(tuple(case["name"] for case in cases) == CD_NAMES and len(lock["sources"]) == len(cases)
            and set(lock["controls"]) == {"before", "after"}, "signed disclosed roster differs")
    return lock, cases


def cd_inputs(folder, name, edited):
    lock, cases = cd_source(folder)
    idx = CD_NAMES.index(name)
    row = lock["sources"][idx]
    slot = folder / f"Slot{idx + 1:02d}"
    require(row["slot"] == idx and row["passed"] is True and row["tree_rows"] == 26 and row["snapshots"] == 4
            and tuple(phase["phase"] for phase in row["phases"]) == CD_PHASES, "incorrect disclosed case lifecycle")
    receipts = [checked_json(slot / phase["phase"] / "Record.json", phase["receipt_sha256"]) for phase in row["phases"]]
    require(all(item["passed"] is True and item["writer_output_count"] == 0 for item in receipts)
            and all(phase["passed"] and phase["checks"] == phase["checks_passed"] > 0
                    for phase in row["phases"]), "source phase is missing its independent numeric acceptance")
    stem = name + ("Edited" if edited else "") + ".SLDPRT"
    data = checked(slot / stem, row["edited_sha256" if edited else "original_sha256"])
    phase = row["phases"][2 if edited else 1]["receipt_sha256"]
    return data, cases[idx], tuple(row["orientation"]), phase


def warm_proof(folder, name, edited, fresh=False):
    from AuditTypedChamfer import (
        KPartitionStream, ReadChmfOwn, ReadActiveNodes, ReadBodyLoop, ReadNativeLink, ReadXmtStages, RequireXmt,
        SldprtArchive, DecodePartData,
    )
    from FilletHistoryBody import vertex_point

    inputs = cd_inputs if fresh else expected_inputs
    data, case, branch, phase = inputs(folder, name, edited)
    candidate_axis, axes, modeled_positive, orders = shape_axes(case)
    schemas = registry()
    denied = guard_runtime()
    proof = inspect(data, case, branch, edited, phase, schemas)
    archive = SldprtArchive.from_bytes(data)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    owners = ReadChmfOwn(link)
    feature = owners.FeatureValue.FieldsValue
    selected, detached = (feature["f888"].FieldsValue["items"][0]["o"], feature["f8a8"])
    wrapper_words = [node.FieldsValue["f68"] for node in (selected, detached)]
    active, history = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    current = ReadActiveNodes(active.data)
    previous = ReadXmtStages(history.data, current, tuple(mark.FieldsValue["f18"] for mark in owners.Controllers))[1].NodesValue
    physical_order = []
    for row in proof["physical"]["stock_support"]["faces_in_archive_order"]:
        face = RequireXmt(previous, row["face_slot"], 14)
        _, fins = ReadBodyLoop(previous, face)
        points = [vertex_point(previous, previous[index].Integer("vertex")) for index in fins]
        normal_axes = [i for i in range(3) if max(p[i] for p in points) - min(p[i] for p in points) < 1e-11]
        (normal,) = normal_axes
        physical_order.append({"normal_axis": "xyz"[normal], "face_ordinal": row["ordinal"],
                               "endpoints": row["endpoints_on_face"]})
    primary = axes[branch[0]]
    reverse = modeled_positive != primary
    native_order = [{key: row[key] for key in ("normal_axis", "face_ordinal")} for row in physical_order]
    require(branch[1] == "tan" and physical_order[0]["normal_axis"] == "xyz"[primary]
            and native_order == orders[reverse] and native_order != orders[not reverse]
            and all(type(word) is int and not word & 128 for word in wrapper_words)
            and feature["f860"] == 0 and proof["exact_linked_replay"] and not denied,
            "source side contrast differs in physical order, entity flip or exact replay")
    return {"case": name, "edited": edited, "source_sha256": digest(data), "native_source_phase_sha256": phase,
            "selected_edge_axis": "xyz"[candidate_axis], "measured_d1_motion_axis": "xyz"[primary],
            "modeled_positive_first_normal_axis": "xyz"[modeled_positive],
            "requires_reciprocal_modeled_side": reverse, "native_support_order": physical_order,
            "modeled_signed_support_orders": {"positive": orders[False], "reciprocal": orders[True]},
            "component_f68_words": wrapper_words, "feature_f860": feature["f860"],
            "exact_linked_replay": True, "guarded_external_accesses": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--case", choices=NAMES + CD_NAMES)
    parser.add_argument("--fresh-cd", action="store_true")
    parser.add_argument("--edited", action="store_true")
    parser.add_argument("--objdump", type=Path)
    parser.add_argument("--model-dll", type=Path)
    parser.add_argument("--part-dll", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    names = CD_NAMES if args.fresh_cd else NAMES
    if args.case is not None:
        require(args.case in names, "case is outside the selected disclosed source lock")
        print(json.dumps(warm_proof(args.disclosed, args.case, args.edited, args.fresh_cd), sort_keys=True))
        return
    require(all((args.model_dll, args.part_dll, args.objdump, args.report)) and not args.report.exists(),
            "supply exact licensed binaries and an unused numeric receipt path")
    installed = binary_owners(args.model_dll, args.part_dll, args.objdump)
    rows = []
    if args.fresh_cd:
        lock, _ = cd_source(args.disclosed)
        for kind, phase in lock["controls"].items():
            control = checked_json(args.disclosed / f"control-{kind}" / "Record.json", phase["receipt_sha256"])
            require(phase["passed"] and control["passed"] is True, "source lock has an unhealthy control")
    for name in names:
        for edited in (False, True):
            command = [sys.executable, "-I", "-B", str(HERE), "--disclosed", str(args.disclosed), "--case", name]
            if args.fresh_cd:
                command.append("--fresh-cd")
            if edited:
                command.append("--edited")
            process = run(command, capture_output=True, timeout=90, check=False)
            require(process.returncode == 0 and not process.stderr, process.stderr.decode())
            rows.append(json.loads(process.stdout))
    require(rows[0]["requires_reciprocal_modeled_side"] and rows[1]["requires_reciprocal_modeled_side"]
            and not rows[2]["requires_reciprocal_modeled_side"] and not rows[3]["requires_reciprocal_modeled_side"],
            "the disclosed calibrated pair does not distinguish the two modeled orientations")
    receipt = {"schema": "kit.sw2026.ordinary-chamfer-signed-source-audit.v1", "installed": installed,
               "disclosed": rows, "guarded_source_processes": len(rows), "native_processes": 0, "writer_outputs": 0}
    if args.fresh_cd:
        receipt.update(raw_source_lock_sha256=CD_LOCK, source_job_sha256=CD_JOB, source_native_lifetimes=8)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
