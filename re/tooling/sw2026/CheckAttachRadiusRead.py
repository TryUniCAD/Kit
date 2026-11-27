from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
TERMINAL = "3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03"
TRIAL = "5d7680db342c5c7e037313d0a2bc3e02820b1d21dfcbdad5cd77293430d32d01"
PREDICTION = "767d0a22a75e92f40a83126516a611b987ecf0c927e70ce9c491c3f37613e15c"
BUILD_HASH = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PHASES = {
    "Frozen": "699be1addf4b644f1ebdeecc6862f65610155d294e10fa6d7cbcf3d6a224f1cd",
    "Working": "d39693d2617c0900a607fb7e6e5be041b7caea906ebcd0cecc69fb8d767a7416",
}
PART_NAME = "DisclosedRadialSceneProbe.SLDPRT"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"unrecognized disclosed input {path.name}")
    return data


def validate_native(result, trial, predict):
    rows = result["phases"]
    require(result["passed"] and result["controls_healthy"] and result["distinct_native_processes"] == 4
            and not result["heldout_acceptance"] and result["packet_sha256"] == TRIAL
            and trial["generated_sha256"]["child"] == PHASES["Frozen"]
            and set(rows) == {"ControlBefore", "Generated", "Reopen", "ControlAfter"},
            "native bracket, locked packet, or result changed")
    for phase, row in rows.items():
        identity = row["oracle_identity"]
        require(row["role"] == phase and row["passed"] and row["immutable_inputs_unchanged"]
                and row["open_errors"] == row["open_warnings"] == 0
                and identity["file_version"] == "34.5.2.0604" and identity["version_matches"]
                and identity["sha256"] == BUILD_HASH, "native phase identity or result changed")
    require(len({row["oracle_identity"]["process_creation_filetime"] for row in rows.values()}) == 4,
            "native bracket lifetimes overlap")
    saved = rows["Generated"]["saved"]["child"]
    require((saved["original_sha256"], saved["native_sha256"], saved["path_basename"], saved["save_status"])
            == (PHASES["Frozen"], PHASES["Working"], PART_NAME, [True, 0, 0]),
            "actual native child save is not bound")
    for name, phase, expected in (("Frozen", "Generated", "initial"), ("Working", "Reopen", "edited")):
        observed = rows[phase]["initial"]
        require(observed["diagnostic_counts"]["child"] == 0
                and observed["configurations"] == [predict["generated"]["parent_configuration"],
                                                   predict["generated"]["child_configuration"]],
                f"native child layout changed in {name}")
        yield (name, observed, predict["generated"][expected]["child"])


def native_comparison(document, lite, link, model, expected, prediction):
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
    from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows

    (sketch,) = document.sketches
    (circle,) = sketch.entities
    radial, fixed = sketch.constraints
    profile, boss = (item for item in document.feature_timeline if item.sketch_id == sketch.id)
    radius, height = (document.parameter(feature.parameter_ids[0]) for feature in (profile, boss))
    (body,) = document.bodies
    (operation,) = model.operations
    require(not document.validate() and not lite.validate() and lite.brep is None
            and (document.parameters, document.feature_timeline, document.sketches)
            == (lite.parameters, lite.feature_timeline, lite.sketches),
            "full and design-only strict SDK reads disagree")
    require(radial.kind == "radius" and radial.driving and radial.parameter_id == radius.id
            and fixed.kind == "fixed" and [(row.entity_id, row.point) for row in fixed.references] == [(circle.id, "center")]
            and sketch.closed_profile_entity_ids == ((circle.id,),)
            and (radius.owner_id, height.owner_id) == (profile.id, boss.id)
            and len(document.parameters) == 2 and radius.name == height.name == "D1"
            and boss.definition.end_condition == "blind" and not boss.definition.reversed
            and boss.definition.second_length is None and boss.definition.length == height.value,
            "strict SDK did not retain the live circle and blind boss history")
    index = IndexFeatures(link)
    owner = ReadExtrude(link, index[operation.object_id], index)
    radial_parameter = NativeRows(NativeRecord(owner.ProfileValue.FieldsValue["pd_f80"].FieldsValue["dims"])["val_g1"])[0]["d"].FieldsValue["f28"]
    depth_parameter = owner.DepthValue.Parameter
    radial_word, depth_word = (item.FieldsValue["f58"] for item in (radial_parameter, depth_parameter))
    require(radius.value.value == radial_word * 1000 and height.value.value == depth_word / 0.001
            and radius.attributes["typed_archive_owner"]["object_index"] == radial_parameter.IndexValue
            and height.attributes["typed_archive_owner"]["object_index"] == depth_parameter.IndexValue,
            "SDK used formatted keywords instead of actual drivers")
    require(body.name == model.SavedCircleName == boss.name
            and body.final_feature_id == boss.id
            and body.attributes["native_object_id"] == operation.object_id
            and document.brep.bodies[0].design_body_id == body.id,
            "physical body is detached from its actual named creator")
    values = {f"D1@{profile.name}": radial_word, f"D1@{boss.name}": depth_word}
    require({key: format(value, ".6g") for key, value in values.items()}
            == {key: format(value, ".6g") for key, value in expected["dimensions_m"].items()},
            "typed drivers differ from native measurements")
    measured = body.topology
    centre = body.attributes["solidworks.body_centroid_mm"]
    metric = {"volume": measured.volume / 1e9, "area": measured.surface_area / 1e6,
              "com": [value / 1000 for value in centre]}
    require((measured.solid_count, measured.face_count, measured.edge_count, measured.vertex_count) == (1, 3, 2, 2),
            "active cylinder topology changed")
    for target in (prediction, expected["mass"]["child"]):
        require([format(value, ".6g") for value in (metric["area"], metric["volume"], *metric["com"])]
                == [format(value, ".6g") for value in (target["area"], target["volume"], *target["com"])],
                "strict SDK body differs from the independent native and model measurements")
    return {"body": body.name, "creator": boss.name,
            "parameter_metres_hex": {key: value.hex() for key, value in values.items()},
            "inactive_depth_m": boss.attributes["solidworks.inactive_blind_depth"]["value_m"],
            "mass": metric, "body_atom": model.SavedCircleAtom,
            "diagnostics": [row.code for row in document.diagnostics],
            "feature_timeline_rows": len(document.feature_timeline),
            "native_observed_tree_rows": len(expected["child_tree"])}


def check_refusals(archive, link, model, opposite):
    from convert.adapters.solidworks.Container.Format import KPartitionStream
    from convert.adapters.solidworks.Core.TypedResolved.Circles.BindSavedCircle import BindSavedCircle
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures

    index = IndexFeatures(link)
    boss = index[model.operations[0].object_id]
    parent = index[model.sketches[0].object_id]
    atom = boss.FieldsValue["f528"]["items"][0]["o"]
    root = link.ConfigValue.RootValue.FieldsValue
    edits = [
        ("producer", boss.FieldsValue["f498"][0], "v", 0),
        ("match_tag", atom.FieldsValue, "f1b0", 0),
        ("visibility", root["ffe0"][0], "v", 1),
        ("selected_mark", boss.FieldsValue["f3d0"].FieldsValue, "f18", 1),
    ]
    if parent.FieldsValue["f3c0"]:
        edits.append(("cache_creator", boss.FieldsValue["f4a8"], "f68", parent))
    failures = {}
    for case, fields, key, attempted in edits:
        original = fields[key]
        fields[key] = attempted
        try:
            BindSavedCircle(model, link, index, parent, archive)
        except ValueError as error:
            failures[case] = str(error)
        else:
            raise ValueError(f"typed SDK accepted wrong {case}")
        finally:
            fields[key] = original
    foreign = replace(archive, records=tuple(
        row if row.name != KPartitionStream else next(x for x in opposite.records if x.name == row.name)
        for row in archive.records))
    try:
        BindSavedCircle(model, link, index, parent, foreign)
    except ValueError as error:
        failures["stale_partition"] = str(error)
    else:
        raise ValueError("typed SDK accepted inactive retained partition")
    return failures


def worker(request):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
    from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KPartitionStream
    from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, DecodePartition
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from CheckSavedCircleRead import linked_streams
    from CheckAttachDimConflict import check_dimension_conflicts
    from interchange.brep.Validation import BrepValidate
    from interchange.document.Models import DocumentProvenance
    from interchange.document.Validation import DocumentFeatureValidate, DocumentReferenceValidate

    root = Path(request["packet"])
    phase = request["phase"]
    other = next(name for name in PHASES if name != phase)
    path = root / phase / PART_NAME
    data = checked(path, PHASES[phase])
    opposite = SldprtArchive.from_bytes(checked(root / other / PART_NAME, PHASES[other]))
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "cp1252"):
        _ = lookup(name)
    active = True
    attempts = []

    def audit(event, _):
        if active and event in {"open", "subprocess.Popen", "os.startfile", "os.spawn", "os.exec",
                                "os.system", "socket.connect", "ctypes.dlopen"}:
            attempts.append(event)
            raise RuntimeError(f"attached radius SDK used runtime input {event}")

    sys.addaudithook(audit)
    try:
        archive = SldprtArchive.from_bytes(data)
        link = ReadNativeLink(archive, 0)
        replay = linked_streams(archive, link)
        model = NativePartModel(archive, None)
        calls = []

        def count_cylinder(frame, event, arg):
            if event == "call" and (
                frame.f_code.co_name in {"CheckSavedRound", "DecodeBrep"}
                and "/solidworks/" in frame.f_code.co_filename.replace("\\", "/")
            ):
                calls.append(frame.f_code.co_name)

        sys.setprofile(count_cylinder)
        try:
            doc = open_document(data, source_format="solidworks.sldprt", strict=True, include_tessellation=False)
        finally:
            sys.setprofile(None)
        require(calls.count("CheckSavedRound") == 1, f"full read repeated cylinder proof: {calls}")
        require(calls.count("DecodeBrep") == 1, f"full read repeated solid decoding: {calls}")
        lite = open_document(data, source_format="solidworks.sldprt", strict=True,
                             include_brep=False, include_tessellation=False)
        observed = native_comparison(doc, lite, link, model, request["native"], request["prediction"])
        active_part, history = DecodePartition(archive.require(KPartitionStream), KPartitionStream)
        physical = DecodeBrep(active_part.data)
        require(physical == replace(doc.brep, bodies=(replace(doc.brep.bodies[0], design_body_id=""),)),
                "strict SDK substituted active physical data")
        nodes = ReadActiveNodes(active_part.data)
        marks = ReadHistMarks(history.data, nodes)
        refusals = check_refusals(archive, link, model, opposite)
        conflicts = check_dimension_conflicts(archive, model) if request.get('geometry_conflicts') else {}
    finally:
        active = False
    require(not attempts and checked(path, PHASES[phase]) == data,
            "guarded runtime I/O or source mutation")
    return {"phase": phase, "file_sha256": PHASES[phase], "linked_streams": replay,
            "physical": {"active_sha256": digest(active_part.data), "rollback_sha256": digest(history.data),
                         "active_nodes": len(nodes), "selected_activation_marks": marks},
            "editable": observed, "refusals": refusals, "runtime_external_accesses": len(attempts),
            **({"physical_driver_conflicts": conflicts} if conflicts else {})}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--geometry-conflicts", action="store_true")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(dumps(worker(loads(sys.stdin.read())), sort_keys=True))
        return
    require(args.packet is not None and args.output is not None, "use actual disclosed packet and new receipt")
    root = args.packet.resolve()
    terminal, trial, predict = (loads(checked(root / name, wanted)) for name, wanted in
                               (("Result.json", TERMINAL), ("Trial.json", TRIAL),
                                ("Evidence/Prediction.json", PREDICTION)))
    cases = []
    for phase, native, prediction in validate_native(terminal, trial, predict):
        data = {"phase": phase, "packet": str(root), "native": native, "prediction": prediction}
        if args.geometry_conflicts:
            data["geometry_conflicts"] = True
        child = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=dumps(data),
                    capture_output=True, text=True, timeout=120, check=False)
        require(child.returncode == 0 and not child.stderr, child.stderr)
        cases.append(loads(child.stdout))
    result = {"schema": "kit.sw2026.attached-radius-sdk-read.v1", "cases": cases,
              "native_identity": {"version": "34.5.2.0604", "sha256": BUILD_HASH},
              "native_result_sha256": TERMINAL, "trial_sha256": TRIAL, "prediction_sha256": PREDICTION,
              "tool_sha256": digest(HERE.read_bytes()), "fresh_processes": len(cases),
              "reported_native_scope": "resolved child in native concentric assembly",
              "native_standalone_acceptance": False, "heldout_credits": 0}
    if args.geometry_conflicts:
        result["schema"] = "kit.sw2026.attached-radius-sdk-read.v2"
        result["conflict_tool_sha256"] = digest(HERE.with_name("CheckAttachDimConflict.py").read_bytes())
    with args.output.open("x", encoding="utf-8") as output:
        output.write(dumps(result, sort_keys=True, indent=2) + "\n")
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
