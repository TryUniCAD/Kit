from argparse import ArgumentParser
from itertools import product
from math import dist, fsum, ulp
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuditPatternEnvelope import (
    ARTIFACTS, CFG, ORACLE, RESOLVED, VERSION, ContainerMo, Obj, SldprtArchive,
    add_envelope_rules, checked, digest, encode, lifecycle, need_node,
    node_name, registry, require, vector,
)
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved_compat, store_resolved_state_compat


PACKET = "60620b7cf6072b729e55f615d4d6e2b14f7e7dfb7a43407303e24e788dc1f328"
NATIVE = "c46b85d6ee72bafcbb438c4f70813966fdcf37331585bdb6970b531fbb21b5be"
NEGATIVE = "2c63cd870f5252e4a80f12ce863d9ca6d0ea20385cf2b46667a6ec76478b6338"
PRINCIPAL_LOCK = "8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426"
ANGLE_PLANE = "moConstraintCoincLineAtAnglePlaneRefplaneData_c"
DEFAULT_PLANE = "moDefaultRefPlnData_c"
ZERO = (0.0, 0.0, 0.0)


def stream_record(value, state):
    return {"bytes": len(value), "sha256": digest(value), "map_next_slot": state.count}


def replay(raw):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "comparison requires the observed ordinary version-19000 native archive")
    reg = add_envelope_rules(registry())
    config = archive.require(CFG)
    resolved = archive.require(RESOLVED)
    doc, read_cfg = load_config(config, reg, VERSION, archive=archive, name=CFG)
    cfg_seed = read_cfg.map_state()
    encoded_cfg, written_cfg = store_config_state(doc, reg, VERSION)
    require(not doc.tail and config == encoded_cfg and cfg_seed.state == written_cfg.state,
            "Config-0 bytes or typed map changed on replay")
    state, read_features = load_resolved_compat(resolved, reg, VERSION, archive=archive, name=RESOLVED, seed=cfg_seed)
    encoded_resolved, written_resolved = store_resolved_state_compat(state, reg, VERSION, seed=written_cfg)
    require(not state.tail and resolved == encoded_resolved
            and read_features.map_state().state == written_resolved.state,
            "ResolvedFeatures bytes or typed map changed on linked replay")
    return doc.roots[0], state.roots, {
        "config": stream_record(config, written_cfg),
        "resolved": stream_record(resolved, written_resolved),
        "both_streams_and_linked_maps_equal": True,
    }


def geometry_fields(model, roots, expected_class):
    (pattern,) = [node for node in roots if isinstance(node, Obj) and node.cls == "moLPattern_c"]
    line = need_node(pattern["f1288"], "moLineRef_w")
    selection = need_node(line["f58"], "moCompRefPlane_c")
    comp = need_node(selection["f58"], "moUnitComponent_c")
    require(comp["owner"] is model and comp is not model["f990"], "selected line has another model owner")
    key = selection["ff0"]["f00"]
    (plane,) = [node for node in roots if isinstance(node, Obj) and node.cls == "moRefPlane_c" and node["f08"] == key]
    data = need_node(plane["f6f8"], expected_class)
    origin = vector(data["root"])
    require(origin == ZERO, "comparison is scoped to a through-origin datum")
    center_field = "display_root" if data.cls == DEFAULT_PLANE else "root"
    display_origin = vector(data[center_field])
    normal = vector(data["normal"])
    transform = data["f20"]
    require(transform["has_matrix"] == 1 and transform["f70"] == 1 and
            (transform["f58"], transform["f60"], transform["f68"]) == ZERO,
            "comparison needs an unscaled rotation at the origin")
    matrix = transform["f08"]
    bases = tuple(tuple(matrix[f"m{3 * j + i}"] for j in range(3)) for i in range(3))
    require(dist(bases[2], normal) <= 1e-15 and all(abs(dist(basis, ZERO) - 1) <= 1e-15 for basis in bases)
            and abs(fsum(a * b for a, b in zip(*bases[:2], strict=True))) <= 1e-15,
            "typed datum display frame is not an orthonormal in-plane basis")
    b0, b1, b2, b3 = (data[f"b{i}"] for i in range(4))
    require(b0 > b1 and b2 > b3, "missing bounded native display rectangle")

    def plane_point(u, v):
        return tuple(fsum((p, u * a, v * b)) for p, a, b in zip(display_origin, *bases[:2], strict=True))

    center_uv = ((b0 + b1) / 2, (b2 + b3) / 2)
    center = plane_point(*center_uv)
    point = vector(line["fc8"])
    error = tuple(actual - predicted for actual, predicted in zip(point, center, strict=True))
    require(all(abs(value) <= ulp(predicted) for value, predicted in zip(error, center, strict=True)),
            "stored line point departs from the selected display centre by more than one component ULP")
    corner = vector(plane["f6c0"])
    require(corner == plane_point(b1, b2), "plane name location did not bind the expected display corner")
    return {
        "plane_name": node_name(plane), "plane_id": key, "plane_archive_object": plane.index,
        "plane_data_archive_object": data.index, "plane_data_class": data.cls,
        "direction_line_object": line.index, "geometry_root_m": origin, "display_origin_field": center_field,
        "display_origin_m": display_origin, "basis_u_v_n": bases, "ordered_borders_m": [b0, b1, b2, b3],
        "rect_corners_model_m": [plane_point(u, v) for u, v in product((b0, b1), (b2, b3))],
        "name_location_f6c0_m": corner, "center_uv_m": center_uv, "center_model_m": center,
        "fc8_point_m": point, "fc8_error_m": error,
        "same_binary64_words": tuple(map(float.hex, center)) == tuple(map(float.hex, point)),
    }


def axis_relation(roots, snap, placement):
    (axis,) = [node for node in roots if isinstance(node, Obj) and node.cls == "moRefAxis_c"
               and node_name(node) == "EnvelopeHinge"]
    data = need_node(axis["f700"], "moPlaneInterAxisData_c")
    start, finish = vector(data["f18"]), vector(data["f30"])
    hinge = snap["datum"]["hinge"]
    require([list(start), list(finish)] == hinge["endpoints_m"]
            and list(vector(data["f50"])) == hinge["unit"] == [0.0, 0.0, -1.0],
            "stored hinge does not match the independently observed through-origin line")
    length = dist(start, finish)
    u_ends = (-finish[2], -start[2])
    pad = length * 0.05
    predicted = (u_ends[0] + pad, u_ends[1] - pad, length + pad, -pad)
    require(dist(predicted, placement["ordered_borders_m"]) <= 2e-17,
            "selected display borders do not follow the hypothesized padded hinge square")
    return {"axis_id": axis["f08"], "endpoints_m": [start, finish], "length_m": length,
            "hypothesis_padded_hinge_square": {"padding_m": pad, "predicted_borders_m": predicted,
                                              "comparison_error_m": dist(predicted, placement["ordered_borders_m"])}}


def prior_principal(directory):
    require(directory.name == "LinearPatternSourcePacket03", "only the prior disclosed principal cohort is permitted")
    lock = json.loads(checked(directory / "Progress" / "disclosed-lock.json", PRINCIPAL_LOCK))
    require(lock["cohort"] == "disclosed" and lock["passed"] and lock["oracle_sha256"] == ORACLE,
            "unqualified prior principal comparison")
    rows = {}
    require([case["name"] for case in lock["cases"]] == ["D01X", "D02Y"], "principal cases differ")
    for case in lock["cases"]:
        label = case["name"]
        plane_name = "Right Plane" if label == "D01X" else "Top Plane"
        names = [label + suffix + ".SLDPRT" for suffix in ("", "Spacing", "Instances")]
        require(case["split"] == "disclosed" and case["passed"] and
                names == [member["name"] for member in case["native_sources"]], "principal artifact roles differ")
        for source in case["native_sources"]:
            name = source["name"]
            raw = checked(directory / "DisclosedNative" / label / name, source["sha256"], source["bytes"])
            model, roots, stats = replay(raw)
            placement = geometry_fields(model, roots, DEFAULT_PLANE)
            require(placement["plane_name"] == plane_name, "principal pattern selected a different actual datum")
            rows[name] = {"sha256": source["sha256"], **stats, "placement": placement}
    return rows


def audit(trial, principal, negative, output):
    require(trial.name == "LinearPatternEnvelope02", "only the disclosed oblique contrast is permitted")
    original = json.loads(checked(negative, NEGATIVE))
    require(original["packet_sha256"] == PACKET and original["native_result_sha256"] == NATIVE
            and original["discriminator"]["disposition"] == "outside_fixed_hypotheses",
            "first negative envelope audit differs")
    manifest, spec, records, payloads = lifecycle(trial, PACKET, NATIVE)
    frame_checks = []
    rows = {}
    for name, phase in zip(ARTIFACTS, ("pristine-reopen", "spacing-reopen"), strict=True):
        raw = payloads[name]
        model, roots, stats = replay(raw)
        old = original["measurements"][name]
        snap = records[phase]["reopened"]
        placement = geometry_fields(model, roots, ANGLE_PLANE)
        require(placement["plane_name"] == spec["direction_datum"]["name"]
                and placement["plane_id"] == old["datum_id"]
                and placement["direction_line_object"] == old["selected_line_object"]
                and list(placement["fc8_point_m"]) == old["fc8_point_m"]
                and placement["same_binary64_words"]
                and stats["config"]["map_next_slot"] == old["config_map_base"]
                and stats["resolved"]["map_next_slot"] == old["resolved_next_slot"]
                and stats["resolved"]["sha256"] == old["resolved_sha256"],
                "new linked placement comparison did not recover the original negative's exact geometry")
        measured = snap["datum"]["transform"]
        require(tuple(tuple(measured[i:i + 3]) for i in (0, 3, 6)) == placement["basis_u_v_n"],
                "typed display frame differs from the native datum frame")
        hinge = axis_relation(roots, snap, placement)
        rows[name] = {"sha256": digest(raw), **stats, "placement": placement, "hinge": hinge,
                      "native_spacing_m": snap["pattern"]["values"]["D1Spacing"],
                      "native_checks": len(records[phase]["checks"]),
                      "original_fc8_span": old["fc8_span"], "original_fc8_ieee754_le_hex": old["fc8_ieee754_le_hex"]}
        frame_checks.append(placement)
    require(frame_checks[0] == frame_checks[1], "spacing edit changed datum presentation or stored line point")
    principal_rows = prior_principal(principal)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "host datum audit loaded CAD runtime")
    result = {
        "schema": "kit.sw2026.linear-pattern-datum-placement.v1",
        "packet_sha256": PACKET, "native_result_sha256": NATIVE, "original_host_audit_sha256": NEGATIVE,
        "principal_source_lock_sha256": PRINCIPAL_LOCK, "research_revision": manifest["research_revision"],
        "audit_sha256": digest(Path(__file__).read_bytes()), "original_discriminator": original["discriminator"],
        "oblique": rows, "principal": principal_rows,
        "exact_config_resolved_and_map_replays": len(rows) + len(principal_rows),
        "native_processes_started_on_host": 0, "heldouts": 0, "generated_parts": 0,
    }
    with output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"receipt_sha256": digest(output.read_bytes()),
                      "exact_config_resolved_and_map_replays": result["exact_config_resolved_and_map_replays"]}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--principal", type=Path, required=True)
    parser.add_argument("--negative", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    audit(arguments.trial, arguments.principal, arguments.negative, arguments.output)
