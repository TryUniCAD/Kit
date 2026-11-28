from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
from functools import partial
import json
from math import isclose
import os
from pathlib import Path
from struct import unpack_from
from subprocess import run
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

import ObserveFirstCreatorNative as native


HOST = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
PROOF_REVISION = "49cec4f02825f4820c44b87569eab67c5cec7756"
SCOPE_PIN = "cb4b092466238addd4d6291a65a78374d2fbcc6ab5d6c0b0345de18a73f6c729"
RECT_PIN = "78a5748c61021a5e526d6b07cf2b27f292755303bf4df0d389c0313b11187277"
BETA_REQUEST = "26c199208ff767bc36d1269a7b86d0974fdfaa9d833aabff1ccbf5a1818871d1"
BETA_CASE = "9c5bf4b6255de6e6dafe74880fd4c5bdcc5607027084ce17a0974f4e447ddd16"
EDIT_DEPTHS_M = {"Single": 0.011625, "Translated": 0.009875}


def helpers():
    import MeasureFirstCreatorScope as proof
    from MeasureSavedEndWords import authority
    from InspectSdkBlindPart import tree_prediction
    return proof, proof.warm, authority, tree_prediction


def approved_inputs(workspace):
    proof, warm, authority, _ = helpers()
    scope = authority(proof.MEASURES / "SdkFirstCreatorScope01.json", SCOPE_PIN)
    rectangle = authority(proof.MEASURES / "SdkRectangleDimensionsNative01.json", RECT_PIN)
    warm.require(scope["source_tree"] == warm.SOURCE_TREE and not scope["new_oracle_acceptance"]
                 and rectangle["passed"] and rectangle["application_usable"] and rectangle["controls_healthy"]
                 and rectangle["heldout_inputs_read"] == 0 and rectangle["oracle_sha256"] == native.ORACLE,
                 "declared inputs do not have the exact prior disclosed authorities")
    references = {name: authority(proof.MEASURES / name, value) for name, value in warm.PINS.items()}
    source = next(warm.models(workspace, references))
    warm.require(source["name"] == "SinglePlate" and source["sha256"] == scope["cases"]["SinglePlate"]["original_sha256"],
                 "first original must be the already measured warm SinglePlate")
    Single = warm.invoke("inspect", source)
    single_request = {**Single["request"], "scope": proof.EXPECTED_SCOPE}
    warm.require(Single["files_unchanged"] and
                 warm.wire_sha(single_request) == scope["cases"]["SinglePlate"]["cold_composition"]["neutral_request_sha256"],
                 "guarded warm projection differs from its existing pure-neutral proof")

    ruled = workspace / "SdkRectDimNative02"
    packet = authority(ruled / "Packet.json", rectangle["packet_sha256"])
    prior = authority(ruled / "Inspection/Result.json", rectangle["raw_result_sha256"])
    beta, = (row for row in packet["cases"] if row["directory"] == "Cases/beta")
    beta_case, = (row for row in prior["cases"] if row["model_name"] == native.CASES["Translated"])
    warm.require(prior["passed"] and prior["oracle_sha256"] == native.ORACLE and prior["controls_healthy"]
                 and prior["packet_sha256"] == rectangle["packet_sha256"] and prior["heldout_inputs_read"] == 0
                 and beta["request_sha256"] == BETA_REQUEST and beta["case_sha256"] == BETA_CASE
                 and beta_case["original_sha256"] == beta["candidate_sha256"] and beta_case["passed"],
                 "independent translated input differs from its earlier guarded native qualification")
    beta_dir = ruled / beta["directory"]
    beta_request = authority(beta_dir / "Request.json", BETA_REQUEST)
    intent = authority(beta_dir / "Case.json", BETA_CASE)
    old = beta_request["rectangle_dimensions"]
    inputs = {
        "Single": {"request": single_request, "authority": {
            "archival_source_sha256": source["sha256"], "native_source_result_sha256": source["native_result_sha256"],
            "exact_projection_receipt_sha256": SCOPE_PIN,
            "label_authority": "source's two declared driver-owned spatial points",
        }},
        "Translated": {"request": {
            "document": beta_request["document"],
            "label_points": [[*old["width_text_m"], 0.000237], [*old["height_text_m"], -0.000419]],
            "dimension_modes": [beta_request["settings"]["design_intent"],
                                beta_request["settings"]["selected_leader"], old["route_centerline"]],
            "scope": proof.EXPECTED_SCOPE,
        }, "authority": {
            "independently_authored_neutral_request_sha256": BETA_REQUEST, "earlier_native_case_sha256": BETA_CASE,
            "earlier_native_result_sha256": rectangle["raw_result_sha256"], "native_discovery_receipt_sha256": RECT_PIN,
            "label_authority": "prior neutral XY and routing, newly authored signed normal coordinate",
        }},
    }
    expected = {name: values["request"]["document"]["metadata"]["name"] for name, values in inputs.items()}
    warm.require(expected == native.CASES and old == intent["presentation"] and beta_case["generated_unchanged"],
                 "the two documented geometry requests are not the declared independent cases")
    seed = ruled / "Control.SLDPRT"
    warm.pinned(seed, native.CONTROL)
    return seed, inputs, scope


def compose(request):
    proof, warm, _, tree_prediction = helpers()
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey

    document = warm.FromData(request["document"])
    sketch, = document.sketches
    feature, = document.feature_timeline
    config, = document.configurations
    support, = (plane for plane in document.support_planes if plane.id == sketch.support_plane_id)
    parameter_ids = (*sketch.parameter_ids, *feature.parameter_ids)
    by_id = {item.id: item for item in document.parameters}
    require = warm.require
    require(len(parameter_ids) == len(set(parameter_ids)) == 3 and set(parameter_ids) == set(by_id),
            "request does not own exactly its two sketch and one depth dimension")
    params = [by_id[identity] for identity in parameter_ids]
    require([parameter.name for parameter in params] == ["D1", "D2", "D1"]
            and [parameter.owner_id for parameter in params] == [sketch.id, sketch.id, feature.id]
            and all(parameter.value.unit == "mm" and parameter.role.value == "driving" for parameter in params),
            "request does not retain three actual editable millimetre dimensions")
    document = replace(document, parameters=tuple(params))
    document.assert_valid()
    warm.InferCaps(document)
    document.to_json()
    name = document.metadata["name"]
    case_id, = (key for key, value in native.CASES.items() if value == name)
    labels, modes = request["label_points"], request["dimension_modes"]
    warm.primed()
    guard = proof.Guard(HERE.parent)
    sys.addaudithook(guard.InspectEvent)
    guard.BeginBuild()
    build = partial(proof.construct, document, labels=labels, modes=modes)
    all_bodies, plan, label_delta = build(proof.FirstCreatorScope(proof.ExistingBodies.All))
    selected, _, selected_label_delta = build(proof.FirstCreatorScope.from_data(request["scope"]))
    require(label_delta == selected_label_delta == [proof.RESOLVED], "scope variants did not separately generate the same spatial text graph")
    require(all_bodies.StreamsValue.keys() == selected.StreamsValue.keys() and len(all_bodies.StreamsValue) == 10,
            "candidate containers do not retain their same ten typed streams")
    differences = [key for key, row in all_bodies.StreamsValue.items() if selected.StreamsValue[key] != row]
    require(differences == [proof.RESOLVED], "scope touched a stream outside the actual feature owner")
    first, second = (candidate.StreamsValue[proof.RESOLVED] for candidate in (all_bodies, selected))
    change, = (index for index, (a, b) in enumerate(zip(first, second, strict=True)) if a != b)
    require(unpack_from("<i", first, change) == (0,) and unpack_from("<i", second, change) == (1,),
            "scope field differs by more than its authored word")
    owners = tuple(proof.read_owners(value)[1] for value in (all_bodies, selected))
    require(tuple(owner["scope"] for owner in owners) == (0, 1)
            and proof.replace_owner_scope(owners[0]) == proof.replace_owner_scope(owners[1])
            and owners[0]["feature"]["offset"] <= change < owners[0]["feature"]["end"] - 3,
            "scope word does not belong to the distinct actual first boss")
    locator = proof.CASE_LOCATOR + name + ".SLDPRT"
    for candidate in (all_bodies, selected):
        archive = warm.SldprtArchive.from_bytes(candidate.BytesValue)
        header = warm.ReadNativeLink(archive, 0).ConfigValue.HeaderValue
        self_file = warm.RequireNative(header.FieldsValue["f38"], "moExtObject_c")
        require(ReadFileKey(self_file)[1:3] == (locator, 2), "embedded part self-file locator differs")
    displays = tuple(warm.observe(candidate.BytesValue, sketch.name) for candidate in (all_bodies, selected))
    require(displays[0] == displays[1] and
            [displays[0][key]["text_m"] for key in ("width", "height")] == labels
            and all(row["centerline_route"] is modes[2] for row in displays[0].values()),
            "independent readback did not preserve both modeled spatial label owners")
    values = [item.value.value / 1000 for item in params]
    vertices = [list(point) for point in plan.VerticesValue]
    kind = native.predict(vertices, values[2])
    require(all(isclose(vertices[2][i] - vertices[0][i], values[i], rel_tol=2e-12) for i in range(2)),
            "authored rectangle edges differ from their associated drivers")
    direct, history = proof.public_history(all_bodies.BytesValue, include_brep=True)
    measured = warm.measure_boundary(direct.brep, direct.bodies[0].id,
                                     tuple(tuple(1000 * item for item in vertex) for vertex in vertices), params[2].value.value)
    require(history["operation"] == "create" and history["constraints"] == 6
            and isclose(measured["volume_mm3"] * 1e-9, kind["volume"], rel_tol=2e-12),
            "baseline strict typed cold geometry disagrees with the independent neutral dimensions")
    recipe = warm.MakePartRecipe(plan, warm.TARGET_INSTANT)
    system = recipe.SystemValue
    tree = tree_prediction({"settings": {"system": {"folders": system.FolderValues, "planes": dict(system.PlaneNames),
                                                     "cabinet_name": system.CabinetName, "origin_name": system.OriginName}}},
                           {"intent": {"profile": sketch.name, "feature": feature.name,
                                       "resolved_roots": len(all_bodies.ResolvedValue.RootsValue)}})
    require(not guard.DeniedReads, "pure candidate generation attempted a native runtime or data read")
    return {
        "case_id": case_id, "model_name": name, "profile": sketch.name, "feature": feature.name,
        "support": support.name, "configuration": config.name,
        "parameter_names": [f"{parameter.name}@{node.name}" for parameter, node in zip(params, (sketch, sketch, feature), strict=True)],
        "dimensions_m": values, "vertices_m": vertices, "tree": tree,
        "label_xyz_m": labels, "label_routing": modes[2], "runtime_input_reads": len(guard.DeniedReads),
        "epoch": warm.TARGET_INSTANT, "input_locator": locator,
        "scope_only_stream": differences[0], "scope_byte_offset": change, "scope_byte_values": [0, 1],
        "same_streams": 9, "complete_stream_count": 10, "actual_display_owners": displays[0],
        "first_creator_owners": list(owners), "all_scope_strict_geometry": measured,
        "candidate_bytes": {mode: b64encode(value.BytesValue).decode()
                            for mode, value in zip(native.MODES, (all_bodies, selected), strict=True)},
    }


def inner(op, request):
    child = run((sys.executable, "-I", "-B", str(HERE), op), input=native.wire(request),
                capture_output=True, timeout=110)
    native.require(child.returncode == 0 and not child.stderr,
                   f"guarded scope {op} failed: {child.stderr.decode(errors='replace')[-3500:]}")
    return json.loads(child.stdout)


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)


def current_tool(phase_tool):
    _, warm, _, _ = helpers()
    relative = phase_tool.relative_to(warm.ROOT).as_posix()
    current = phase_tool.read_bytes()
    native.require(warm.git("show", f"HEAD:{relative}") == current, "frozen tool is not its exact committed source")
    return current


def freeze(workspace):
    proof, warm, _, _ = helpers()
    require = native.require
    require(os.name != "nt" and workspace.resolve(strict=True) == HOST, "freeze the exact disclosed host workspace")
    require(warm.git("rev-parse", "HEAD:src").decode().strip() == warm.SOURCE_TREE
            and not warm.git("status", "--porcelain", "--", "src"), "candidate construction must use its committed SDK tree")
    work = workspace / native.PACKET_NAME
    require(not work.exists(), "earlier scope evidence must remain immutable")
    seed, inputs, old = approved_inputs(workspace)
    revision = warm.git("rev-parse", "HEAD").decode().strip()
    helpers_path = [HERE, HERE.with_name("MeasureFirstCreatorScope.py"), HERE.with_name("MeasureWarmNestedLeaf.py"),
                    HERE.with_name("MeasureSavedEndWords.py"), HERE.with_name("WarmLeafBoundary.py"),
                    HERE.with_name("MeasureNestedReadback.py"), warm.TOOLS / "InspectSdkBlindPart.py",
                    warm.TOOLS / "AuthorRectangleAnchors.py", HERE.with_name("TraceFirstCreatorScope.py"),
                    HERE.with_name("TraceSavedEndWords.py"), *(warm.ROOT / name for name in warm.BOUND_TOOLS)]
    host_tools = {path.relative_to(warm.ROOT).as_posix(): warm.digest(current_tool(path)) for path in helpers_path}
    previous_tool = HERE.with_name("MeasureFirstCreatorScope.py").relative_to(warm.ROOT).as_posix()
    require(host_tools[previous_tool] == old["tool_sha256"]["MeasureFirstCreatorScope.py"] ==
            warm.digest(warm.git("show", f"{PROOF_REVISION}:{previous_tool}")), "independent scope constructor changed")
    tool_sources = {name: current_tool(HERE.with_name(name) if name == "ObserveFirstCreatorNative.py" else warm.TOOLS / name)
                    for name in native.TOOLS}
    predictions = {}
    for name, group in inputs.items():
        one, two = (inner("build", group["request"]) for _ in range(2))
        require(one == two and one["case_id"] == name, "two fresh pure constructors did not agree")
        predictions[name] = one
    single = predictions["Single"]
    past = old["cases"]["SinglePlate"]["cold_composition"]
    require(warm.digest(b64decode(single["candidate_bytes"]["All"], validate=True)) == past["control_sha256"]
            and warm.digest(b64decode(single["candidate_bytes"]["Selected"], validate=True)) == past["selected_sha256"],
            "earlier measured SinglePlate builder bytes changed")
    neg = dict(inputs["Single"]["request"])
    neg["scope"] = {**neg["scope"], "prior_body_ids": ["unrelated-body"]}
    rejected = inner("reject", neg)
    require(rejected["rejected"] and rejected["construction_runtime_reads"] == 0, "negative guard did not refuse a prior body")
    work.mkdir(mode=0o700, exist_ok=False)
    tools = {}
    for name, raw in tool_sources.items():
        target = work / "Tools" / name
        write_new(target, raw)
        tools[name] = native.file_row(work, target)
    control = work / "Inputs/Control.SLDPRT"
    control.parent.mkdir(exist_ok=False)
    native.copy_new(seed, control, native.CONTROL)
    cases = {}
    for name, group in inputs.items():
        data = predictions[name]
        encoded = data.pop("candidate_bytes")
        artifact = data["model_name"] + ".SLDPRT"
        modes = {}
        for mode, number in native.MODES.items():
            target = work / "Inputs" / name / mode / artifact
            write_new(target, b64decode(encoded[mode], validate=True))
            modes[mode] = {"scope_word": number, "input": native.file_row(work, target),
                           "derivative_locator": str(native.GUEST_WORK / "Trials" / name / mode / "Edited" / artifact)}
        request_file = work / "Proof" / name / "Request.json"
        write_new(request_file, native.wire(group))
        proof_file = work / "Proof" / name / "Build.json"
        write_new(proof_file, native.wire({**data, "modes": modes, "deterministic_guarded_builds": 2,
                                         "request_sha256": native.digest(request_file)}))
        edit = EDIT_DEPTHS_M[name]
        cases[name] = {key: data[key] for key in (
            "model_name", "profile", "feature", "support", "configuration", "parameter_names", "dimensions_m",
            "vertices_m", "tree", "label_xyz_m", "label_routing", "runtime_input_reads", "input_locator",
            "scope_only_stream", "scope_byte_offset", "scope_byte_values",
        )} | {
            "edited_depth_m": edit, "expected": {
                "open": native.predict(data["vertices_m"], data["dimensions_m"][2]),
                "edited": native.predict(data["vertices_m"], edit),
            }, "modes": modes, "request": native.file_row(work, request_file), "proof": native.file_row(work, proof_file),
        }
    job = {
        "schema": native.SCHEMA, "guest_path": str(native.GUEST_PACKET), "guest_workspace": str(native.GUEST_WORK),
        "oracle": {"sha256": native.ORACLE, "file_version": native.BUILD},
        "tools": tools, "control": native.file_row(work, control), "cases": cases, "phases": list(native.PHASES),
        "constructor_revision": revision, "writer_source_tree": warm.SOURCE_TREE,
        "constructor_tools_sha256": host_tools, "first_creator_research_revision": PROOF_REVISION,
        "first_creator_research_receipt_sha256": SCOPE_PIN,
        "guarded_pair_builds": 4, "guarded_source_processes": 1, "guarded_negative": rejected,
        "heldout_inputs_read": 0, "native_processes_started": 0, "accepted_native_cases": 0,
    }
    pin = native.publish(work / "Packet.json", job)
    result = run((sys.executable, "-I", "-B", str(work / "Tools/ObserveFirstCreatorNative.py"), "verify",
                  str(work / "Packet.json"), "--packet-sha256", pin), capture_output=True, text=True, timeout=30)
    require(result.returncode == 0 and not result.stderr and json.loads(result.stdout)["verified"],
            "standalone packet observer did not verify: " + result.stderr)
    return {"packet_sha256": pin, "host_packet": str(work / "Packet.json"), "guest_packet": str(native.GUEST_PACKET),
            "construction_source_commit": revision, "candidate_sha256": {
                key: {mode: item["input"]["sha256"] for mode, item in row["modes"].items()} for key, row in cases.items()
            }, "native_processes_started": 0, "heldout_inputs_read": 0}


def reject(request):
    proof, warm, _, _ = helpers()
    doc = warm.FromData(request["document"])
    scope = proof.FirstCreatorScope.from_data(request["scope"])
    warm.primed()
    guard = proof.Guard(HERE.parent)
    sys.addaudithook(guard.InspectEvent)
    guard.BeginBuild()
    error = warm.refusal(lambda: proof.construct(doc, scope, request["label_points"], request["dimension_modes"]),
                         "ValueError", "standalone first creator cannot select an existing body")
    return {"rejected": error, "construction_runtime_reads": len(guard.DeniedReads)}


def saved(job):
    proof, warm, _, _ = helpers()
    path = Path(job["file"])
    raw = warm.pinned(path, job["sha256"], job["bytes"])
    warm.primed()
    guard = warm.FrozenReads({path})
    sys.addaudithook(guard.inspect)
    archive = warm.SldprtArchive.from_bytes(raw)
    link = warm.ReadNativeLink(archive, 0)
    features = warm.IndexFeatures(link)
    warm.CheckSingleBoss(features, "moExtrusion_c")
    boss, = (row for row in features.values() if row.ClassValue.NameValue == "moExtrusion_c")
    owner = warm.ReadExtrude(link, boss, features)
    fields = boss.FieldsValue
    part = link.ConfigValue.RootValue
    manager = part.FieldsValue["fd88"]
    atom = warm.ReadOutputAtom(boss)
    identity = warm.NativeNodeId(boss)
    require = warm.require
    require(manager["n6c"] == 1 and manager["atoms"][0]["o"] is atom
            and part.FieldsValue["fd90"]["n"] == 0
            and atom.FieldsValue["f12c"] == atom.FieldsValue["f130"] == identity
            and warm.ReadNativeName(boss) == job["feature"], "native save lost its actual sole first-creator output owner")
    _, _, marks = warm.ReadBodyKernel(archive.require(warm.PARTITION), warm.PARTITION)
    warm.CheckThinMarks(part, boss, marks)
    typed_depth = owner.RequireDepth().DepthValue.native_value
    pointer = fields.get("f548")
    display = warm.observe(raw, job["profile"])
    labels = [display[axis]["text_m"] for axis in ("width", "height")]
    guard.active = False
    warm.pinned(path, job["sha256"], job["bytes"])
    require(not guard.denied, "typed post-save proof used undeclared data")
    checks = {
        "saved_scope_word_retained": fields["f544"] == job["scope"],
        "saved_has_no_prior_scope_wrapper": fields["has_f548"] == fields["has_f530"] == 0 and pointer is None,
        "saved_live_depth_retained": isclose(typed_depth, job["depth_m"], rel_tol=2e-7, abs_tol=1e-12),
        "saved_signed_text_normal_retained": all(isclose(observed[2], wanted[2], rel_tol=2e-7, abs_tol=1e-12)
                                                 for observed, wanted in zip(labels, job["label_xyz_m"], strict=True)),
        "saved_centerline_route_retained": all(row["centerline_route"] is job["label_routing"] for row in display.values()),
    }
    return {"sha256": job["sha256"], "passed": all(checks.values()), "checks": checks,
            "stored_existing_body_scope": fields["f544"], "selected_wrapper_present": fields["has_f548"],
            "typed_feature_id": identity, "typed_profile_id": warm.NativeNodeId(owner.ProfileValue),
            "actual_sole_body_atom_id": atom.FieldsValue["f140"], "typed_marks": list(marks),
            "typed_depth_m": typed_depth, "stored_label_xyz_m": labels, "file_unchanged": True}


def qualify(packet, expected, result_sha, target):
    root, job = native.verify(packet, expected)
    _, warm, _, _ = helpers()
    native.require(warm.git("rev-parse", "HEAD:src").decode().strip() == job["writer_source_tree"]
                   and not warm.git("status", "--porcelain", "--", "src")
                   and all(warm.digest(current_tool(warm.ROOT / name)) == pin
                           for name, pin in job["constructor_tools_sha256"].items()),
                   "typed save verification requires its frozen current SDK and host tools")
    result_path = root / "Native/Result.json"
    native.require(result_path.is_file() and result_path.resolve(strict=True) == result_path
                   and native.digest(result_path) == result_sha and not target.exists(), "exact native result or unused output is required")
    native_result = json.loads(result_path.read_bytes())
    native.require(native_result["schema"] == native.SCHEMA and native_result["packet_sha256"] == expected
                   and native_result["packet_inputs_unchanged"] and native_result["heldout_inputs_read"] == 0,
                   "native result does not bind the fixed disclosed inputs")
    phases = native_result["phases"]
    native.require(set(phases) <= set(native.PHASES), "native result contains an unplanned phase")
    for name, row in phases.items():
        relative = "Native/Records/" + ("Trials/" if "/" in name else "") + name + "/Record.json"
        native.checked(root, row["record"], relative)
    reports = {}
    for case, group in job["cases"].items():
        for mode, number in native.MODES.items():
            key = case + "/" + mode
            if key not in native_result["derivatives"]:
                continue
            row = native_result["derivatives"][key]
            path = native.checked(root, row, f"Native/Derivatives/{key}/{group['model_name']}.SLDPRT")
            edit, reopen = (phases[key + "/" + label] for label in ("Edit", "Reopen"))
            native.require(edit["passed"] and reopen["passed"] and edit["derivative_sha256"] == reopen["input_sha256"] == row["sha256"],
                           "saved proof requires successful matching edit and fresh reopen authority")
            try:
                report = inner("saved", {"file": str(path), **{field: row[field] for field in ("sha256", "bytes")},
                                         "depth_m": group["edited_depth_m"], "scope": number,
                                         **{field: group[field] for field in ("feature", "profile", "label_xyz_m", "label_routing")}})
            except ValueError as error:
                reports[key] = {"sha256": row["sha256"], "passed": False, "diagnostic": str(error)}
                continue
            report["native_ids_match"] = [report["typed_profile_id"], report["typed_feature_id"]] == reopen["states"]["Initial"]["native_ids"]
            report["passed"] &= report["native_ids_match"]
            reports[key] = report
    typed_saved = (native_result["all_native_lifecycles_passed"] and len(reports) == 4
                   and all(row["passed"] for row in reports.values()))
    outcome = {"schema": native.SCHEMA + ".saved-proof", "packet_sha256": expected, "native_result_sha256": result_sha,
               "controls_healthy": native_result["controls_healthy"], "native_scope_getters_passed": native_result["passed"],
               "all_native_lifecycles_passed": native_result["all_native_lifecycles_passed"],
               "guarded_typed_saved_replays": len(reports), "reports": reports,
               "typed_saved_checks_passed": typed_saved, "passed": native_result["passed"] and typed_saved,
               "whole_original_source_transfer": False, "heldout_acceptance": False, "public_writer_qualified": False}
    pin = native.publish(target, outcome)
    print(json.dumps({"passed": outcome["passed"], "sha256": pin, "guarded_saved_replays": len(reports)}))
    return int(not outcome["passed"])


def main():
    if len(sys.argv) == 2 and sys.argv[1] in {"build", "reject", "saved"}:
        print(json.dumps({"build": compose, "reject": reject, "saved": saved}[sys.argv[1]](json.load(sys.stdin)),
                         ensure_ascii=False, allow_nan=False))
        return 0
    parser = ArgumentParser(description="Freeze and qualify the disclosed first-creator scope experiment")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--workspace", type=Path, default=HOST)
    qualifier = commands.add_parser("qualify")
    qualifier.add_argument("packet", type=Path)
    qualifier.add_argument("--packet-sha256", required=True)
    qualifier.add_argument("--native-result-sha256", required=True)
    qualifier.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "qualify":
        return qualify(args.packet, args.packet_sha256, args.native_result_sha256, args.output)
    print(json.dumps(freeze(args.workspace), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
