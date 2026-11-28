from argparse import ArgumentParser
from base64 import b64decode
import json
from pathlib import Path
from subprocess import run
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from AuditSavedSweepMain import BASE, BASE_SRC, LOCK, ORACLE, SHARED, SHARED_SRC, checked, demand, digest, disclosed, scratch_sdk

PRIOR = "12d52bafff3388fb6272a013b191f1a1220a9800029949e3aad828a6812c8d24"


def native_measurement(directory, job):
    phase = job["native_phase"]
    name = f"Slot{job['slot']:02d}-{phase['phase']}.json"
    record = json.loads(checked(directory / name, phase["sha256"]))
    identity = record["oracle_identity"]
    demand(identity["file_version"] == "34.5.2.0604" and identity["sha256"] == ORACLE
           and record["passed"] and record["source_immutable"]
           and record["native_sha256"] == job["file_sha256"]
           and record["writer_output_count"] == 0 and not record["dialogs"],
           "disclosed geometry measurement does not belong to the exact native source")
    mass = record["last_high_accuracy_mass"]
    demand(mass["selected_solid"] and mass["use_system_units"] and not mass["manual_overrides"],
           "native geometry measurement has an alternate body, unit or material domain")
    return {"mass": {key: mass[key] for key in ("volume", "area", "com", "mass")},
            "bodies": record["last_body_count"], "faces": record["last_body_faces"]}


def read_worker(sdk):
    sys.path.insert(0, str(sdk))
    import SavedSweepReplay
    from SavedSweepOwners import by_type
    from SavedTorusActive import active_replay, saved_rim_owners
    from SavedTorusGeometry import result_geometry, saved_profiles
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime

    job = json.load(sys.stdin)
    payload = b64decode(job.pop("payload"), validate=True)
    native = job.pop("native_measurement")
    expected_partition = job.pop("active_sha256")
    demand(digest(payload) == job["file_sha256"], "topology worker did not receive the locked input")
    base = SavedSweepReplay.semantic_owners

    def complete_owners(archive, config, manager, resolved, drivers):
        previous = base(archive, config, manager, resolved, drivers)
        nodes, torus, wire = active_replay(archive)
        demand(wire["active_sha256"] == expected_partition and wire["active_nodes"] == 92,
               "active saved result does not match the previously verified partition")
        sweep, = by_type(resolved, "moSweep_c")
        creator = previous["feature_id"]
        rims, topology = saved_rim_owners(nodes, torus, previous["atom"]["id"], creator,
                                          DatumTime(config.HeaderValue, creator))
        material = config.RootValue.FieldsValue["f1420"]
        density = material.FieldsValue["f08"]
        demand(density.ClassValue.NameValue == "moDensityParameter_c"
               and density.FieldsValue["f58"] == topology["density"],
               "active physical body density does not retain its actual configuration value")
        geometry = result_geometry(archive, torus, rims, topology, drivers, native)
        sketches = saved_profiles(config, resolved, sweep, drivers)
        return {**previous, "active_replay": wire, "topology": topology, "geometry": geometry,
                "saved_sketches": sketches}

    SavedSweepReplay.semantic_owners = complete_owners
    state = SavedSweepReplay.inspect(payload, job)
    return {key: state[key] for key in (
        "slot", "role", "file_sha256", "native_phase", "streams", "maps", "runtime_accesses",
        "active_replay", "topology", "geometry", "saved_sketches",
    )}


def edit_responses(states):
    results = []
    for slot in (1, 2):
        original, section, path = (row for row in states if row["slot"] == slot)
        demand((original["role"], section["role"], path["role"]) == ("original", "section", "path"),
               "invalid disclosed edit lifecycle order")
        start_seam, section_seam, path_seam = (row["saved_sketches"][0] for row in (original, section, path))
        demand(start_seam["permanent_marks"] == section_seam["permanent_marks"] == path_seam["permanent_marks"]
               and start_seam["seam_angle_rad"] == path_seam["seam_angle_rad"] == 0.0
               and section_seam["seam_angle_rad"] > 0.0,
               "independent source edit did not retain the actual periodic handle identity")
        for edited, changed_index, signs in ((section, 1, (1, -1)), (path, 0, (1, 1))):
            base_radii = original["geometry"]["radii_m"]
            radii = edited["geometry"]["radii_m"]
            demand(radii[1 - changed_index] == base_radii[1 - changed_index]
                   and radii[changed_index] > base_radii[changed_index],
                   "independent edit moved a non-owning result radius")
            before = original["geometry"]["measures"]["native"]
            after = edited["geometry"]["measures"]["native"]
            delta = {key: after[key] - before[key] for key in ("volume", "area", "mass")}
            center = tuple(b - a for a, b in zip(before["com"], after["com"], strict=True))
            demand(all(value > 0 for value in delta.values())
                   and all(value * sign > 0 for value, sign in zip(center[:2], signs, strict=True)),
                   "observed one-factor edit has the wrong geometric response")
            results.append({"slot": slot, "edit": edited["role"], "radius_delta_m": radii[changed_index] - base_radii[changed_index],
                            "section_seam_turn_rad": edited["saved_sketches"][0]["seam_angle_rad"],
                            "metric_delta_si": delta, "centroid_delta_m": center})
    return results


def supervise(directory):
    _, jobs = disclosed(directory)
    prior_path = HERE.parents[3] / "solidworks/measurements/2026/ScopedSavedSweepReplay01.json"
    prior = json.loads(checked(prior_path, PRIOR))
    sources = {(state["slot"], state["role"]): state for state in prior["states"]}
    with TemporaryDirectory(prefix="KitSavedSweepTopology") as scratch:
        sdk = Path(scratch)
        scratch_sdk(sdk)
        states = []
        for job in jobs:
            state = sources[job["slot"], job["role"]]
            demand(state["file_sha256"] == job["file_sha256"], "previous result cohort changed")
            job["active_sha256"] = state["physical_result"]["partition_sha256"]
            job["native_measurement"] = native_measurement(directory, job)
            proc = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(sdk / "src")),
                       input=json.dumps(job), encoding="utf-8", capture_output=True, timeout=45, check=False)
            demand(proc.returncode == 0 and not proc.stderr, proc.stderr or proc.stdout)
            states.append(json.loads(proc.stdout))
    methods = (HERE, HERE.with_name("SavedTorusActive.py"), HERE.with_name("SavedTorusGeometry.py"))
    return {"schema": "kit.sw2026.saved-sweep-topology.v1", "baseline": BASE,
            "baseline_src": BASE_SRC, "shared_archive": SHARED, "shared_src": SHARED_SRC,
            "prior_receipt_sha256": PRIOR, "disclosed_lock_sha256": LOCK,
            "method_sha256": {value.name: digest(value.read_bytes()) for value in methods},
            "oracle_build": "34.5.2.0604", "oracle_sha256": ORACLE, "python": sys.version.split()[0],
            "zlib": ZLIB_RUNTIME_VERSION, "new_cad_processes": 0, "published_archives": 0,
            "heldout_credits": 0, "fresh_sdk_processes": len(states), "states": states,
            "independent_edit_responses": edit_responses(states)}


if __name__ == "__main__":
    parser = ArgumentParser(description="Audit the actual typed torus and periodic rims of the six disclosed saved sweeps")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--disclosed", type=Path)
    modes.add_argument("--worker", type=Path)
    args = parser.parse_args()
    result = read_worker(args.worker) if args.worker else supervise(args.disclosed)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
