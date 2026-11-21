from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from subprocess import run
import sys


def audit(name, mode, source, source_lock):
    from AuditStockSketchProjection import exact, require
    from AuditThroughAllDisclosed import mutate
    from convert import open_document
    from interchange import CadDocument
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.geometry.Models.GeometryCurves import CircleGeometry

    file, digest, stock_caption, _, build, _ = source
    payload = exact(file, digest)
    if mode not in ("path", "bytes"):
        modified = mutate(payload, mode)
        rejected = open_document(
            modified,
            source_format="solidworks.sldprt",
            include_brep=False,
            include_tessellation=False,
        )
        graph = rejected.metadata["solidworks.typed_resolved_semantics"]
        require(graph["status"] == "unsupported", "malformed cut graph qualified")
        return {"rejected": True, "typed_diagnostic": graph["diagnostic"]}

    case_name, state = name.split("/")
    state_name = f"reopen-{state}"
    directory = file.parents[2]
    public_path = (
        directory.parents[1] / "Progress" / case_name / state_name / "Record.json"
    )
    proof = source_lock["phase_records"][state_name]
    public = json.loads(exact(public_path, proof["public_record_sha256"]))
    native_file = directory / f"{state_name}.json"
    native_digest = public["private_record_sha256"]
    actual = json.loads(exact(native_file, native_digest))["result"]["initial"]
    native_cut, native_boss = actual["operation"], actual["stock"]
    require(
        native_cut["end_forward"] == 1 and native_cut["dimensions"] == [],
        "native source has an active cut parameter",
    )
    require(
        native_cut["depth_forward_m"] == native_cut["depth_reverse_m"] == 0.0,
        "native source has a finite cut depth",
    )
    document = open_document(
        file if mode == "path" else payload, source_format="solidworks.sldprt"
    )
    require(
        not document.validate()
        and document.brep is not None
        and len(document.bodies) == 1,
        "strict public model or saved body did not qualify",
    )
    boss, cut = [
        row
        for row in document.feature_timeline
        if str(row.operation) in ("join", "cut")
    ]
    require(
        isinstance(boss.definition, ExtrudeFeature)
        and isinstance(cut.definition, ExtrudeFeature),
        "public history did not retain both extrusion definitions",
    )
    require(
        boss.definition.end_condition == ExtrudeEnd.KMidPlane
        and boss.definition.symmetric,
        "stock mid plane rule was lost",
    )
    depth = boss.definition.length
    require(
        depth is not None
        and depth.unit == "mm"
        and isclose(
            depth.value, native_boss["depth_forward_m"] * 1000.0, abs_tol=1e-10
        ),
        "stock depth differs from the native driver",
    )
    params = {value.id: value for value in document.parameters}
    (stock_param,) = [params[key] for key in boss.parameter_ids]
    require(
        stock_param.value == depth and stock_param.owner_id == boss.id,
        "stock depth does not retain its actual driver",
    )
    selected = cut.definition
    second = ExtrudeEnd.KThroughAll if native_cut["both_directions"] else None
    require(
        selected.end_condition == ExtrudeEnd.KThroughAll
        and selected.reversed == native_cut["reverse_direction"]
        and selected.length is selected.second_length is None
        and selected.second_end_condition == second
        and not cut.parameter_ids
        and not any(value.owner_id == cut.id for value in params.values()),
        "public cut lost its direction or invented a depth parameter",
    )
    require(
        boss.id in cut.input_feature_ids
        and document.bodies[0].final_feature_id == cut.id,
        "actual stock and body history are unbound",
    )
    sketch = {value.id: value for value in document.sketches}
    profile = sketch[cut.sketch_id]
    (circle,) = [
        entity.geometry
        for entity in profile.entities
        if isinstance(entity.geometry, CircleGeometry)
    ]
    (native_circle,) = actual["profiles"][profile.name]["geometry"]
    require(
        not profile.constraints
        and not profile.parameter_ids
        and all(
            isclose(value, metres * 1000.0, rel_tol=0.0, abs_tol=1e-10)
            for value, metres in zip(
                (circle.center.x, circle.center.y, circle.radius),
                (*native_circle["center"], native_circle["radius"]),
                strict=True,
            )
        ),
        "the actual cut profile did not retain its three free circle values",
    )
    stock = sketch[boss.sketch_id]
    require(
        stock.name == stock_caption
        and stock.attributes["typed_line_loop"] is True
        and len(stock.constraints) == 4,
        "typed stock contour was lost",
    )
    graph = document.metadata["solidworks.typed_resolved_semantics"]
    body = graph["cut_body_dependency"]
    require(
        body["binding"] == "saved_configuration_atom_alias"
        and body["consumed_atom_id"] != body["result_atom_id"],
        "the cut body selection and output were not resolved",
    )
    cut_evidence = next(
        value
        for value in graph["extrusions"]
        if value["end_condition"] == "through_all"
    )
    require(
        cut_evidence["end_owner"]["class"] == "moEndSpec_c"
        and "parameter_owner" not in cut_evidence,
        "through all provenance did not bind the actual depthless end",
    )
    decoded = CadDocument.from_json(document.to_json(indent=None))
    rebuilt = next(value for value in decoded.feature_timeline if value.id == cut.id)
    require(
        not decoded.validate() and rebuilt == cut and decoded.bodies == document.bodies,
        "neutral wire changed the selected cut history",
    )
    _ = exact(file, digest)
    return {
        "source_sha256": digest,
        "native_phase_sha256": native_digest,
        "oracle_file_version": build,
        "stock_depth_mm": depth.value,
        "end_condition": selected.end_condition,
        "reverse_direction": selected.reversed,
        "second_end_condition": selected.second_end_condition,
        "cut_parameters": len(cut.parameter_ids),
        "profile_center_radius_mm": [circle.center.x, circle.center.y, circle.radius],
        "body_aliases": dict(body),
        "exact_neutral_cut_wire": True,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker", nargs=2)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    sys.path[:0] = [str(repository / "src"), str(Path(__file__).resolve().parent)]
    from AuditStockSketchProjection import disclosed, require, source_fingerprint

    cases = {
        name: row
        for name, row in disclosed(
            repository, args.source_root.resolve(strict=True)
        ).items()
        if "/" in name
    }
    require(
        len(cases) == 6, "the public through all audit requires six disclosed states"
    )
    lock = (
        repository
        / "re"
        / "solidworks"
        / "v2026"
        / "heldout"
        / "ThroughAllSourceLock01.json"
    )
    slots = {
        value["slot"]: value
        for value in json.loads(lock.read_bytes())["slots"]
        if not value["heldout"]
    }
    if args.worker:
        name, mode = args.worker
        result = audit(name, mode, cases[name], slots[name.split("/")[0]])
        print(json.dumps(result, sort_keys=True))
        return
    faults = (
        "active-distance",
        "second-distance",
        "second-end",
        "chooser-owner",
        "consumes-output",
        "wrapper-atom",
    )
    fingerprint = source_fingerprint(repository)
    specs = [(name, mode) for name in cases for mode in ("path", "bytes")]
    specs.extend(("D01/source", mode) for mode in faults)
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = {
            (name, mode): executor.submit(
                run,
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).resolve()),
                    str(repository),
                    str(args.source_root),
                    str(args.output),
                    "--worker",
                    name,
                    mode,
                ],
                text=True,
                capture_output=True,
                timeout=60,
            )
            for name, mode in specs
        }
        for case, job in jobs.items():
            outcome = job.result()
            require(outcome.returncode == 0, outcome.stderr)
            results[case] = json.loads(outcome.stdout)
    for name in cases:
        require(
            results[name, "path"] == results[name, "bytes"],
            "path and byte cut histories diverged",
        )
    require(
        fingerprint == source_fingerprint(repository),
        "sdk source changed during the measurements",
    )
    proof = {
        "schema": "kit.sw2026.disclosed-public-through-all-read.v1",
        "states": {name: results[name, "path"] for name in cases},
        "physical_diagnostic_faults": {
            name: results["D01/source", name] for name in faults
        },
        "sdk_processes": len(results),
        "source_fingerprint": fingerprint,
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "heldout_inputs_read": 0,
        "new_native_processes": 0,
        "writer_outputs": 0,
        "passed": True,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(proof, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
