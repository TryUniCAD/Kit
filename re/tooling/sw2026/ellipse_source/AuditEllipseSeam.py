from argparse import ArgumentParser
import json
from math import atan2, degrees, hypot, isclose
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(ROOT / "src"), str(HERE.parent / "revolve/EndModes")]

from AuditRevEndOwners import guard_runtime
from EllipseArchiveGrammar import parse_link
from EllipseArchiveOwners import difference, dot, resolve_row
from EllipseModel import require
from EllipsePacket import BUILD, CONTROLS, ORACLE, digest, pinned_json, sha
from EllipseSeamPacket import DESTINATIONS, RESULT, verify
from RunEllipseSeam import PHASES, PHASE_SCHEMA, SCHEMA, exact
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

PROFILE_NAME, BOSS_NAME = "EllipseProfile", "EllipseBoss"
STAGES = {
    "author-sketch": ("draw_open", "sketch_closed", "before_save", "after_save"),
    "author-boss": ("draw_open", "sketch_closed", "boss_created", "before_save", "after_save"),
    "reopen-sketch": ("reopened_cold", "reopened_rebuilt"),
    "reopen-boss": ("reopened_cold", "reopened_rebuilt"),
}
POSITION_TOLERANCE = 1e-10


def near(actual, expected):
    return all(isclose(a, b, rel_tol=0, abs_tol=POSITION_TOLERANCE) for a, b in zip(actual, expected, strict=True))


def custody(packet, job_pin, capture, result_pin):
    job, plan = verify(packet, job_pin)
    require(job["host_audit_sha256"] == sha(Path(__file__).resolve()),
            "host seam analysis differs from the frozen method")
    exact_tree = subprocess.check_output(("git", "-C", str(ROOT), "rev-parse", job["revision"] + "^{tree}"))
    require(exact_tree.decode().strip() == job["tree"], "frozen ellipse archive source tree is unavailable")
    subprocess.run(("git", "-C", str(ROOT), "diff", "--quiet", job["revision"], "--", "src",
                    "re/tooling/sw2026/ellipse_source", "re/tooling/sw2026/revolve/EndModes/AuditRevEndOwners.py"),
                   check=True)
    result = pinned_json(capture / RESULT, result_pin)
    controls, phases = result["controls"], result["phases"]
    require(result["passed"] and result["schema"] == SCHEMA and result["job_sha256"] == job_pin
            and result["revision"] == job["revision"] and result["tree"] == job["tree"]
            and result["oracle_build"] == BUILD and result["oracle_sha256"] == ORACLE
            and result["inputs_unchanged"] and result["idle_after"] and result["writer_output_count"] == 0
            and result["distinct_processes"] == result["fresh_processes"] == 8
            and set(phases) == set(PHASES) and set(controls) == {
                f"control-{side}-{Path(name).stem}" for side in ("before", "after") for name in CONTROLS
            } and all(row["passed"] and row["exit_code"] == 0 for row in controls.values()),
            "ellipse seam source acquisition was incomplete or had unhealthy controls")
    pinned_json(capture / "RegisteredApi.json", result["registered_api_sha256"])
    sources = {}
    for role, filename in DESTINATIONS.items():
        source = capture / filename
        raw = source.read_bytes()
        pin = digest(raw)
        require(pin == result["native_artifacts"][role], "native saved artifact is not the terminal snapshot")
        records = []
        for operation in ("author", "reopen"):
            phase = f"{operation}-{role}"
            row = phases[phase]
            record = pinned_json(capture / phase / "Record.json", row["record_sha256"])
            require(row["passed"] and row["artifact_sha256"] == record["artifact_sha256"] == pin
                    and row["input_sha256"] == (pin if operation == "reopen" else None)
                    and record["job"] == {key: row[key] for key in ("phase", "job_sha256", "control", "input_sha256")}
                    and record["schema"] == PHASE_SCHEMA and record["passed"] and record["immutable"]
                    and record["writer_output_count"] == 0 and exact(record["oracle_identity"])
                    and tuple(stage["stage"] for stage in record["seam_stages"]) == STAGES[phase],
                    "native seam phase does not match the exact source or measured order")
            records.append(record)
        sources[role] = (pin, raw, records)
    return plan, sources


def native_position(centre, major, minor, position):
    u, v = difference(major, centre), difference(minor, centre)
    relative = difference(position, centre)
    cosine, sine = dot(relative, u) / dot(u, u), dot(relative, v) / dot(v, v)
    require(isclose(hypot(cosine, sine), 1, rel_tol=0, abs_tol=1e-7),
            "reported seam position is outside the measured ellipse")
    return degrees(atan2(sine, cosine))


def archived(archive, role, plan):
    link, observations = parse_link(archive)
    features = IndexFeatures(link)
    profile, = [node for node in features.values() if node.ClassValue.NameValue == "moProfileFeature_c"]
    require(ReadNativeName(profile) == PROFILE_NAME, "native seam archive selected a foreign profile")
    frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, features)
    require(tuple((item.x, item.y, item.z) for item in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis))
            == ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), "native ellipse archive has alternate support")
    bosses = [node for node in features.values() if node.ClassValue.NameValue == "moExtrusion_c"]
    require(len(bosses) == int(role == "boss"), "native saved stream differs from its phase role")
    if bosses:
        owner = ReadExtrude(link, bosses[0], features)
        require(owner.ProfileValue is profile and ReadNativeName(owner.NodeValue) == BOSS_NAME
                and owner.ModeValue.value == "blind" and not owner.IsReversed and owner.SecondValue is None
                and owner.RequireDepth().DepthValue.native_value == plan["states"][0]["depth_m"],
                "native boss archive lacks its actual forward blind driver")
    shape = resolve_row(link, RequireNative(profile.FieldsValue["pd_f80"], "sgSketch"), observations)
    points = {key: shape["points"][index] for key, index in shape["point_bindings"].items()}
    for name, expected in zip(("Center", "Major", "Minor"), plan["points_m"], strict=True):
        require(near((*points[name]["coordinates_m"], 0), expected), "saved shape differs from its frozen axis points")
    seam = points["Seam"]
    coords = (*seam["coordinates_m"], 0)
    phase = native_position(*(tuple(point) for point in plan["points_m"]), coords)
    return {
        "seam_id": seam["persistent_words"], "seam_xyz_m": coords, "seam_phase_degrees": phase,
        "seam_ordinal": shape["point_bindings"]["Seam"], "handle_index": seam["handle_index"],
        "ellipse_id": shape["segment_fields"]["f0c"], "profile_points": {
            name: {"id": point["persistent_words"], "xyz_m": (*point["coordinates_m"], 0)}
            for name, point in points.items() if name in ("Center", "Major", "Minor")},
        "config_seed": link.ConfigValue.MapValue.CounterValue,
        "resolved_next": link.ResolvedValue.MapValue.CounterValue,
    }


def live_stage(stage, saved):
    profile = stage["ellipse"]
    require(profile["segment_id"][-1] == saved["ellipse_id"]
            and all(near(profile["points_m"][name], point["xyz_m"]) and
                    profile["point_ids"][name][-1] == point["id"][-1]
                    for name, point in saved["profile_points"].items()),
            "live and saved point roles or ellipse identity differ")
    direct = [row["point"] for row in stage["endpoints"].values() if row["status"] == "observed"]
    axis_ids = tuple(profile["point_ids"].values())
    eligible = [row for row in direct if row["id"][-1] == saved["seam_id"][-1] and row["id"] not in axis_ids]
    shared_endpoint = (eligible[0] if len(eligible) == len(direct) > 0
                       and all(point["id"] == eligible[0]["id"] for point in eligible) else None)
    channels = {}
    for method, row in (stage["endpoints"] | stage["inventories"]).items():
        points = [row["point"]] if "point" in row else row.get("points", [])
        same = [point for point in points if shared_endpoint is not None and point["id"] == shared_endpoint["id"]]
        require(all(near(point["xyz_m"], shared_endpoint["xyz_m"])
                    and point["point_type"] == shared_endpoint["point_type"] for point in same),
                "native live seam channels disagree for the same scoped point")
        channels[method] = {"status": row["status"], "point_ids": [point["id"] for point in points],
                            "point_creation_matches": [point for point in points
                                                       if point["id"][-1] == saved["seam_id"][-1]
                                                       and point["id"] not in axis_ids]}
    output = {"stage": stage["stage"], "channels": channels}
    if shared_endpoint is None:
        return output | {"binding": "archive_seam_not_bound"}
    coords = shared_endpoint["xyz_m"]
    phase = native_position(*(profile["points_m"][name] for name in ("Center", "Major", "Minor")), coords)
    return output | {"binding": "owned_ellipse_endpoint", "live_point_id": shared_endpoint["id"],
                     "xyz_m": coords, "phase_degrees": phase,
                     "matches_saved": near(coords, saved["seam_xyz_m"])}


def digest_roles(sources, plan):
    outcomes = {}
    for role, (pin, raw, records) in sources.items():
        try:
            saved = archived(SldprtArchive.from_bytes(raw), role, plan)
        except BodyUnsupported as error:
            outcomes[role] = {"sha256": pin, "archive_status": "unresolved_typed_shape", "diagnostic": str(error)}
            continue
        author, reopened = ([live_stage(stage, saved) for stage in record["seam_stages"]] for record in records)
        transitions = []
        for group, stages in (("author", author), ("fresh_reopen", reopened)):
            visible = [row for row in stages if row["binding"] == "owned_ellipse_endpoint"]
            transitions.extend([group, first["stage"], second["stage"]] for first, second in zip(visible, visible[1:])
                               if first["live_point_id"] == second["live_point_id"] and not near(first["xyz_m"], second["xyz_m"]))
        outcomes[role] = {"sha256": pin, "archive_status": "linked_typed", "saved": saved, "author": author,
                          "fresh_reopen": reopened, "owned_live_position_changes": transitions}
    one, two = outcomes["sketch"], outcomes["boss"]
    both = all(row["archive_status"] == "linked_typed" for row in outcomes.values())
    return {"cases": outcomes, "both_archives_linked": both,
            "saved_xyz_equal": near(one["saved"]["seam_xyz_m"], two["saved"]["seam_xyz_m"]) if both else None}


if __name__ == "__main__":
    parser = ArgumentParser(description="Compare calibrated native ellipse seam snapshots with their actual stored owner")
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--result-pin", required=True)
    args = parser.parse_args()
    plan, sources = custody(args.job, args.pin, args.capture, args.result_pin)
    external = guard_runtime()
    measurement = digest_roles(sources, plan)
    require(not external, "offline ellipse seam analysis attempted an external access")
    print(json.dumps({"schema": "kit.sw2026.ellipse-seam-discriminator-analysis.v1",
                      "job_sha256": args.pin, "native_result_sha256": args.result_pin,
                      "native_launches": 0, "runtime_external_accesses": len(external),
                      "writer_output_count": 0, **measurement}, sort_keys=True, indent=2))
