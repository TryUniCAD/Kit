from argparse import ArgumentParser
from base64 import b64decode
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from interchange.serialization.Deserialize import FromData

ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCE_JOB = "3289913b17116604a52279a8dca2aba788ec173a2a9f89472605ba699960c477"
TOOLS = ("AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "MaterialSourceFacts.py",
         "OracleIdentity.py", "Swapp.py")


def digest(value):
    return sha256(value).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, "pinned input differs: " + str(path))
    return data


def geometry(document):
    sketch, = document.sketches
    feature, = document.feature_timeline
    positions = [(edge.geometry.start.x * 0.001, edge.geometry.start.y * 0.001) for edge in sketch.entities]
    xs, ys = zip(*positions, strict=True)
    require(len(set(positions)) == 4 and len(set(xs)) == len(set(ys)) == 2,
            "probe intent must be an authored millimetre rectangle")
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    depth = feature.definition.length.value * 0.001
    ids = {sketch.id: sketch.name, feature.id: feature.name}
    drivers = {parameter.name + "@" + ids[parameter.owner_id]: parameter.value.value * 0.001
               for parameter in document.parameters}
    require(len(drivers) == 3 and isclose(drivers["D1@" + feature.name], depth, rel_tol=1e-12),
            "probe geometry and the explicit native driving lengths must agree")
    return {"volume": width * height * depth, "area": 2 * (width * height + width * depth + height * depth),
            "com": [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, depth / 2]}, list(ids.values()), drivers


def freeze(probes, source, out, guest):
    guest = PureWindowsPath(guest)
    require(guest.is_absolute() and guest.drive == "C:" and out.parent.is_dir() and not out.exists(),
            "probe needs a fresh output and an absolute local C: destination")
    source_job = json.loads(checked(source / "Job.json", SOURCE_JOB))
    require(source_job["oracle_sha256"] == ORACLE and source_job["cohort_role"] == "discovery",
            "probe control and helper source must be the disclosed packet")
    control = checked(source / "Control.SLDPRT", source_job["control_sha256"])
    tools = {name: checked(source / "Tools" / name, source_job["tools_sha256"][name]) for name in TOOLS}
    runner = Path(__file__).with_name("RunAssignedMaterialProbe.py")
    tools[runner.name] = runner.read_bytes()
    order = ["AlUnassigned", "AlPart", "AlConfiguration", "AlIdentity", "AlAll", "SteelAll"]
    models, cases = {}, {}
    for name in order:
        input_bytes = (probes / (name + ".Input.json")).read_bytes()
        build_bytes = (probes / (name + ".Build.json")).read_bytes()
        request, built = json.loads(input_bytes), json.loads(build_bytes)
        doc = FromData(request["document"])
        material, = doc.materials
        config, = doc.configurations
        measured, features, drivers = geometry(doc)
        native = PureWindowsPath(request["settings"]["output"]["path_name"])
        require(native == guest / "Models" / (name + ".SLDPRT") and doc.metadata["name"] == name,
                "probe self path differs from the exact intended native candidate locator")
        model = b64decode(built["artifact_base64"], validate=True)
        catalog = request["assignment"]["catalog"]
        require(len(model) == built["bytes"] and digest(model) == built["sha256"]
                and built["runtime_file_access_attempts"] == 0 and built["typed_readback"]["exact_linked_streams"] == 3
                and built["requested_density"] == material.Density
                and built["requested_identity"] == catalog + "|" + material.name
                and built["mode"] == request["mode"],
                "exact model and guarded probe receipt differ")
        models[name] = model
        cases[name] = {"bytes": len(model), "sha256": digest(model), "mode": request["mode"],
                       "input_sha256": digest(input_bytes), "build_sha256": digest(build_bytes),
                       "configuration": config.name, "geometry": measured, "feature_names": features,
                       "drivers_m": drivers, "catalog": catalog, "material": material.name,
                       "density_kg_m3": material.Density}
    (out / "Tools").mkdir(parents=True, exist_ok=False)
    (out / "Models").mkdir(exist_ok=False)
    for name, content in tools.items():
        (out / "Tools" / name).write_bytes(content)
    for name, content in models.items():
        (out / "Models" / (name + ".SLDPRT")).write_bytes(content)
    (out / "Control.SLDPRT").write_bytes(control)
    job = {"schema": "kit.sw2026.assigned-material-probe-job.v1", "guest_root": str(guest),
           "oracle_sha256": ORACLE, "control_sha256": digest(control),
           "tools_sha256": {name: digest(content) for name, content in tools.items()},
           "order": order, "cases": cases}
    data = json.dumps(job, sort_keys=True, allow_nan=False, indent=2).encode("utf-8") + b"\n"
    (out / "Job.json").write_bytes(data)
    return {"job_sha256": digest(data), "staged_candidates": len(models), "native_processes": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("probes", type=Path)
    parser.add_argument("control_packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--guest-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.probes, args.control_packet, args.output, args.guest_dir), sort_keys=True))
