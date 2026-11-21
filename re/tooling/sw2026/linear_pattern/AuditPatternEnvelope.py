from argparse import ArgumentParser
from math import dist, isfinite, ulp
from pathlib import Path
from struct import pack
from subprocess import check_output
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src"), str(TOOLS / "serial")]

from Classes import registry
from Core import ArchiveError, Obj
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved_compat, store_resolved_state_compat
from PatternEnvelopePacket import BUILD, CONTROL, ORACLE, PHASES, checked, digest, encode, require, verify
from PatternEnvelopeWire import add_envelope_rules
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


CFG = "Contents/Config-0"
RESOLVED = CFG + "-ResolvedFeatures"
VERSION = 19000
TOLERANCE = 5e-9
ARTIFACTS = ("DirectionEnvelope.SLDPRT", "DirectionEnvelopeSpacing.SLDPRT")


def node_name(node):
    owner = node.get("f18")
    value = owner.get("f08") if isinstance(owner, Obj) else None
    return value[1] if isinstance(value, tuple) and len(value) == 2 and value[0] == "A" else value


def vector(value):
    values = tuple(value[axis] for axis in "xyz")
    require(all(type(number) is float and isfinite(number) for number in values), "nonfinite or untyped native vector")
    return values


def need_node(value, name):
    require(isinstance(value, Obj) and value.cls == name and value.schema == 1,
            "unexpected source object role " + name)
    return value


def binding_snapshot(data, label):
    snap = data[label]
    views = snap["pattern"]
    return {
        "tree": snap["tree"], "plate": snap["plate_profile"], "seed": snap["seed_profile"],
        "plate_boss": snap["plate_boss"], "seed_boss": snap["seed_boss"],
        "direction": snap["datum"]["signed_normal"], "plane_origin": snap["datum"]["origin_m"],
        "plane_feature": views["plane_feature_reference"]["hex"],
        "seed_feature": views["seeds"][0]["reference"]["hex"],
        "pattern_parents": views["parents"],
        "active_drivers": {name: value.split("@")[:2] for name, value in views["dimensions"]["bindings"].items()},
        "unchanged_values": {name: value for name, value in views["values"].items() if name != "D1Spacing"},
    }


def lifecycle(root, freeze, result_sha):
    packet = root / "Packet"
    manifest = verify(packet, freeze)
    result_home = root / "DisclosedTrial"
    summary = json.loads(checked(result_home / "Result.json", result_sha))
    require(summary["schema"] == "kit.sw2026.linear-pattern-envelope-native.v1"
            and summary["packet_sha256"] == freeze and summary["research_revision"] == manifest["research_revision"]
            and summary["cohort"] == "disclosed" and summary["native_build"] == BUILD
            and summary["oracle_sha256"] == ORACLE and summary["native_lifecycle_passed"]
            and summary["packet_unchanged"] and summary["artifacts_unchanged"]
            and summary["application_pids_before"] == summary["application_pids_after"] == []
            and summary["writer_output_count"] == summary["heldout_sources_accessed"] == 0
            and summary["distinct_processes"] == 6, "unqualified disclosed native phases")
    checked(result_home / "RegisteredApi.json", summary["metadata_sha256"])
    processes = {}
    payloads = {}
    for role, receipt in summary["controls"].items():
        require(role in ("before", "after") and receipt["passed"], "unexpected or unhealthy control")
        row = json.loads(checked(result_home / ("Control" + role.title() + ".json"), receipt["record_sha256"]))
        identity = row["oracle_identity"]
        require(row["opened"] and row["rebuilt"] and row["sha256"] == CONTROL and not row["dialogs"]
                and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
                and row["open_errors"] == row["open_warnings"] == row["whats_wrong"] == 0,
                "control did not bracket this exact oracle")
        processes[role] = identity["process_creation_filetime"]
    rows = summary["phases"]
    require(tuple(row["phase"] for row in rows) == PHASES, "incomplete lifecycle phases")
    records = {}
    for row in rows:
        phase = row["phase"]
        value = json.loads(checked(result_home / phase / "Record.json", row["sha256"]))
        identity = value["oracle_identity"]
        require(row["passed"] and value["passed"] and value["source_immutable"]
                and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
                and not value["application_pids_before"] and not value["application_pids_after"]
                and not value["dialogs"] and not value["first_failure"] and len(value["checks"]) > 0
                and all(check["passed"] for check in value["checks"]), "candidate phase changed or is unhealthy")
        if phase != "author":
            require(value["open"] == {"opened": True, "errors": 0, "warnings": 0}, "native open was unclean")
        processes[phase] = identity["process_creation_filetime"]
        records[phase] = value
        if phase in ("author", "spacing-edit"):
            save = value["save"]
            require(save["ok"] and save["errors"] == save["warnings"] == 0, "native save warned or refused")
            require(save["artifact"] == value["artifact"], "immediate save and closed artifact pins differ")
    order = [processes[name] for name in ("before", *PHASES, "after")]
    require(order == summary["process_creation_filetimes"] and order == sorted(set(order)),
            "six distinct exact-build native processes did not bracket the saves")
    require(tuple(item["name"] for item in summary["artifacts"]) == ARTIFACTS, "unexpected artifact inventory")
    for artifact, save, reopen in zip(summary["artifacts"], ("author", "spacing-edit"),
                                     ("pristine-reopen", "spacing-reopen"), strict=True):
        require(records[save]["artifact"] == records[reopen]["artifact"] == artifact, "lifecycle owns different native bytes")
        payloads[artifact["name"]] = checked(result_home / artifact["name"], artifact["sha256"], artifact["bytes"])
    baseline = binding_snapshot(records["pristine-reopen"], "reopened")
    require(all(binding_snapshot(records[phase], label) == baseline
                for phase, label in (("spacing-edit", "pre_edit"), ("spacing-edit", "edited"), ("spacing-reopen", "reopened"))),
            "same source seed, datum or feature ownership differs across the live spacing edit")
    require(records["author"]["authored"]["tree"] == baseline["tree"], "native author/reopen tree differs")
    return manifest, json.loads((packet / "Spec.json").read_bytes()), records, payloads


def read_graph(raw):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION, "wrong native part format")
    reg = add_envelope_rules(registry())
    with reg.track_usage("load", CFG, role="linked_map_seed", sources=archive.streams) as cfg_usage:
        config, config_reader = load_config(archive.require(CFG), reg, VERSION, archive=archive, name=CFG)
    linked_seed = config_reader.map_state()
    with reg.track_usage("load", RESOLVED, role="oblique_pattern", sources=archive.streams) as load_usage:
        doc, loading = load_resolved_compat(archive.require(RESOLVED), reg, VERSION,
                                            archive=archive, name=RESOLVED, seed=linked_seed)
    with reg.track_usage("store", RESOLVED, role="oblique_pattern") as store_usage:
        rewritten, emitted = store_resolved_state_compat(doc, reg, VERSION, seed=linked_seed)
    require(not config.tail and not doc.tail and rewritten == archive.require(RESOLVED)
            and loading.count == emitted.count, "typed native linked replay has unread or different bytes")
    usages = [item.snapshot() for item in (cfg_usage, load_usage, store_usage)]
    require(all(item["completed"] and not item["missing_schemas"] for item in usages),
            "one decoder direction lacks a complete typed observation")
    require(all(row["completed"] and row["schema"] == "dm.FUN_4bd03960" and row["field"] == "data"
                and row["declared_length"] == row["observed_length"]
                and row["observed_length"] % 8 == 0
                for item in usages[1:] for row in item["raw_operations"]),
            "unexpected opaque field in the exact archive comparison")
    return archive, config.roots[0], doc.roots, {
        "config_map_base": linked_seed.count, "resolved_next_slot": loading.count,
        "surrounding_provisional_schemas": sorted({name for item in usages for name in item["provisional_schemas"]}),
        "raw_display_arrays_per_direction": [len(item["raw_operations"]) for item in usages[1:]],
        "resolved_sha256": digest(rewritten), "resolved_bytes": len(rewritten),
    }


def capture(raw, snapshot, spec):
    archive, model, roots, flags = read_graph(raw)
    patterns = [value for value in roots if isinstance(value, Obj) and value.cls == "moLPattern_c"]
    (pattern,) = patterns
    line = need_node(pattern["f1288"], "moLineRef_w")
    plane_ref = need_node(line["f58"], "moCompRefPlane_c")
    component = need_node(plane_ref["f58"], "moUnitComponent_c")
    datum_id = plane_ref["ff0"]["f00"]
    (plane,) = [value for value in roots if isinstance(value, Obj) and value.cls == "moRefPlane_c"
                and value["f08"] == datum_id and node_name(value) == spec["direction_datum"]["name"]]
    angle_data = plane["f6f8"]
    require(angle_data.cls in ("moConstraintCoincLineAtAnglePlaneRefplaneData_c", "moRefAtAngleData_c")
            and component["owner"] is model and component is not model.get("f990")
            and plane_ref.get("ff8") is None and pattern.get("f1290") is None
            and pattern["f1298"] == int(snapshot["datum"]["reverse"]),
            "typed line lacks its actual registered oblique plane selection or polarity")
    headers = [ReadHeaderGraph(archive.require(name), VERSION) for name in ("Header2", CFG + "-ModelHeader")]
    epoch = plane_ref["ff0"]["f08"]
    require(all(DatumTime(header, datum_id) == epoch for header in headers), "datum creation event does not join the actual native headers")
    native_ref = bytes.fromhex(snapshot["pattern"]["plane_feature_reference"]["hex"])
    require(len(native_ref) == snapshot["pattern"]["plane_feature_reference"]["bytes"]
            and int.from_bytes(native_ref[-4:], "little") == datum_id, "native selected plane reference disagrees with the archive datum")
    (entry,) = pattern["f988"]["items"]
    seed = need_node(entry["o"], "moICE_c")
    require(any(value is seed for value in roots) and node_name(seed) == snapshot["pattern"]["seeds"][0]["name"],
            "archive pattern seed is not the observed feature owner")
    point, direction = vector(line["fc8"]), vector(line["fe0"])
    signed = tuple((-1 if pattern["f1298"] else 1) * value for value in direction)
    require(dist(signed, snapshot["datum"]["signed_normal"]) <= 1e-10
            and dist(vector(angle_data["root"]), snapshot["datum"]["origin_m"]) <= 1e-9,
            "native line or plane root does not match the actual measured frame")
    end = line.end
    require(type(end) is int and type(line.pos) is int and 0 <= line.pos < end - 49,
            "typed line has no complete point/vector/flag tail span")
    offset = end - 49
    data = archive.require(RESOLVED)
    require(data[offset:end] == pack("<6dB", *point, *direction, line["ff8"]),
            "native bytes at the typed line suffix do not equal its model fields")
    return {
        **flags, "file_sha256": digest(raw), "pattern_id": pattern["f08"], "pattern_object": pattern.index,
        "seed_id": seed["f08"], "datum_id": datum_id, "datum_class": angle_data.cls, "datum_epoch": epoch,
        "selected_component_object": component.index, "selected_line_object": line.index,
        "line_bounds": [line.pos, end], "fc8_span": [offset, offset + 24],
        "fc8_point_m": point, "fc8_ieee754_le_hex": data[offset:offset + 24].hex(),
        "fe0_signed_model": signed, "datum_normal_magnitude": dist(direction, (0., 0., 0.)),
    }


def classify(measurements, records, spec):
    pre = spec["ownership_hypotheses"]["pre_pattern_AABB"]
    post = spec["ownership_hypotheses"]["post_pattern_AABB_for_edited_spacing"]
    if len(measurements) != 2 or any("refusal" in value for value in measurements.values()):
        return {"disposition": "typed_source_unresolved"}
    initial, edited = (measurements[name] for name in ARTIFACTS)
    require((initial["datum_id"], initial["seed_id"], initial["datum_epoch"])
            == (edited["datum_id"], edited["seed_id"], edited["datum_epoch"]),
            "stored source identities changed during spacing-only experiment")
    close_initial = dist(initial["fc8_point_m"], pre)
    delta_pre, delta_post = (dist(edited["fc8_point_m"], value) for value in (pre, post))
    matched = close_initial <= TOLERANCE
    if matched and delta_post <= TOLERANCE:
        disposition = "supports_final_envelope"
    elif matched and delta_pre <= TOLERANCE:
        disposition = "agrees_with_pre_pattern_or_retained_point"
    else:
        disposition = "outside_fixed_hypotheses"
    return {"disposition": disposition, "comparison_tolerance_m": TOLERANCE,
            "initial_distance_m": close_initial, "edited_distance_from_pre_m": delta_pre,
            "edited_distance_from_final_m": delta_post,
            "edited_difference_ulp_from_final_formula": [
                (actual - predicted) / ulp(predicted) for actual, predicted in zip(edited["fc8_point_m"], post, strict=True)
            ],
            "observed_prior_extents_m": records["author"]["pre_pattern"]["bounds"]["minmax"],
            "observed_final_extents_m": records["spacing-reopen"]["reopened"]["bounds"]["minmax"]}


def audit(root, packet_sha, result_sha, output):
    manifest, spec, records, payloads = lifecycle(root, packet_sha, result_sha)
    revision = manifest["research_revision"]
    check_output(("git", "merge-base", "--is-ancestor", revision, "HEAD"), cwd=ROOT)
    require(not check_output(("git", "diff", "--name-only", revision, "--", "src", "re/tooling/sw2026/serial"), cwd=ROOT),
            "host archive decoder differs from the pinned packet baseline")
    measurements = {}
    for name, phase in zip(ARTIFACTS, ("pristine-reopen", "spacing-reopen"), strict=True):
        raw = payloads[name]
        try:
            measurements[name] = capture(raw, records[phase]["reopened"], spec)
        except (ArchiveError, KeyError, ValueError, TypeError, RuntimeError) as error:
            measurements[name] = {"refusal": str(error), "type": type(error).__name__, "file_sha256": digest(raw)}
    verdict = classify(measurements, records, spec)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "host placement audit loaded a CAD runtime")
    result = {"schema": "kit.sw2026.linear-pattern-envelope-point.v1", "packet_sha256": packet_sha,
              "native_result_sha256": result_sha, "source_revision": revision,
              "audit_sha256": digest(HERE.read_bytes()), "rule_overlay_sha256": digest(HERE.with_name("PatternEnvelopeWire.py").read_bytes()),
              "native_processes_started_on_host": 0, "generated_parts": 0, "heldouts": 0,
              "measurements": measurements, "discriminator": verdict}
    with output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"receipt_sha256": digest(output.read_bytes()), "disposition": verdict["disposition"]}))
    return 1 if verdict["disposition"] == "typed_source_unresolved" else 0


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    raise SystemExit(audit(arguments.trial, arguments.packet_sha256, arguments.result_sha256, arguments.output))
