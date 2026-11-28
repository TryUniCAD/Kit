from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import dist, isclose, pi, prod
from pathlib import Path
from subprocess import run
import sys

CASES = {
    "G01": (
        "GeneratedThroughAll01/GeneratedInput/GeneratedThroughG01.SLDPRT",
        "5cefc9124919cb2d75a141610fa40a23c328d41297eba6aefe4bcb9f185a3115",
        "ab1af759bc64fef7228c6dfbf529e6e0a7dece925aa6c1edfb04419bb912dc4d",
    ),
    "G02": (
        "ThroughAllWriterPreparation01/Process02/Generated/GeneratedThroughG02.SLDPRT",
        "b8e8c47f01777ece61ae07476aa4e0fe3796483eb8a50340624037d2c05b7452",
        "76924d11a97cdd27410a989b1554e998f2e4e9b24dde6dc39469c1d968aa1ab5",
    ),
    "G03": (
        "ThroughAllWriterPreparation01/Process02/Generated/GeneratedThroughG03.SLDPRT",
        "eef937299332a0aadfe88793c3c1e7c78f52a47c23b95da2605a3f660bf1deb3",
        "edaa96554afd2296f087c974db3307af5299ea2b3492c4e673e9b154aa97eaae",
    ),
}


def coordinates(value):
    return value.x, value.y, value.z


def compare_mass(report, reference, require):
    require(
        isclose(report["volume_m3"], reference["volume"], rel_tol=1e-10),
        "reconstructed volume differs",
    )
    require(
        isclose(report["area_m2"], reference["area"], rel_tol=1e-10),
        "reconstructed surface area differs",
    )
    require(
        all(
            isclose(value, target, rel_tol=1e-10, abs_tol=1e-12)
            for value, target in zip(report["com_m"], reference["com"], strict=True)
        ),
        "reconstructed centre of mass or cut handedness differs",
    )


def worker(root, case, mode):
    from AuditStockSketchProjection import exact, require
    from convert import open_document
    from interchange.brep.Curves.BrepCurves import CircleCurve
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature

    relative, source_hash, prediction_hash = CASES[case]
    source = root / relative
    payload = exact(source, source_hash)
    prediction = json.loads(
        exact(
            root
            / "ThroughAllWriterPreparation01"
            / "Inputs"
            / f"{case}Prediction.json",
            prediction_hash,
        )
    )["independent_analytic_geometry"]["source"]
    document = open_document(
        source if mode == "path" else payload, source_format="solidworks.sldprt"
    )
    require(
        not document.validate() and not document.brep_payloads,
        "the default strict reader must reconstruct the solid from history",
    )
    (body,) = document.bodies
    brep, topology = document.brep, body.topology
    require(
        brep is not None and not brep.validate(frozenset((body.id,))),
        "the reconstructed solid is open or invalid",
    )
    require(
        topology.valid and topology.solid_count == prediction["body_count"] == 1,
        "the reconstructed body count differs",
    )
    (cut,) = [
        feature
        for feature in document.feature_timeline
        if str(feature.operation) == "cut"
    ]
    definition = cut.definition
    require(
        isinstance(definition, ExtrudeFeature)
        and definition.end_condition == ExtrudeEnd.KThroughAll
        and definition.second_end_condition
        == (ExtrudeEnd.KThroughAll if case == "G03" else None)
        and definition.length is definition.second_length is None
        and not cut.parameter_ids
        and body.final_feature_id == cut.id,
        "reconstruction changed the depthless feature history",
    )
    size = len(brep.faces), len(brep.edges), len(brep.vertices)
    require(
        size == (7 if case == "G03" else 8, 14, 10), "the circular cut topology differs"
    )
    lower, upper = coordinates(topology.bounding_box.minimum), coordinates(
        topology.bounding_box.maximum
    )
    box_volume = prod(end - start for start, end in zip(lower, upper, strict=True))
    box_center = tuple(
        (start + end) * 0.5 for start, end in zip(lower, upper, strict=True)
    )
    first, second = [curve for curve in brep.curves if isinstance(curve, CircleCurve)]
    rims = coordinates(first.center), coordinates(second.center)
    require(first.radius == second.radius, "reconstructed circular rims changed radius")
    cavity_volume = pi * first.radius**2 * dist(*rims)
    cavity_center = tuple((start + end) * 0.5 for start, end in zip(*rims, strict=True))
    require(
        isclose(topology.volume, box_volume - cavity_volume, rel_tol=1e-10),
        "the independently measured brep volume differs",
    )
    center = [
        (box_volume * first - cavity_volume * second)
        / (box_volume - cavity_volume)
        * 0.001
        for first, second in zip(box_center, cavity_center, strict=True)
    ]
    result = {
        "source_sha256": source_hash,
        "prediction_sha256": prediction_hash,
        "topology": size,
        "volume_m3": topology.volume * 1e-9,
        "area_m2": topology.surface_area * 1e-6,
        "com_m": center,
        "reconstructed_rim_centers_mm": rims,
        "native_geometry_payloads": len(document.brep_payloads),
        "frozen_analytic_prediction_matched": True,
    }
    compare_mass(result, prediction, require)
    if case == "G01":
        directory = root / "GeneratedThroughAll02" / "Inspection"
        oracle_hash = "a7a14451eb72a459aa70ff9937c996880cc3a8427ac90dcd6d49245187215dff"
        record = json.loads(exact(directory / "Result.json", oracle_hash))
        require(
            record["passed"] and record["controls_healthy"],
            "native generated part lacks healthy controls",
        )
        phase_hash = record["phases"]["Generated"]["record_sha256"]
        phase = json.loads(exact(directory / "Generated" / "Record.json", phase_hash))[
            "result"
        ]
        require(
            phase["input_sha256"] == source_hash,
            "oracle inspected another generated input",
        )
        compare_mass(result, phase["initial"]["mass"], require)
        result["native_result_sha256"] = oracle_hash
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker", nargs=2)
    args = parser.parse_args()
    repository, root = args.repository.resolve(strict=True), args.source_root.resolve(
        strict=True
    )
    sys.path[:0] = [str(repository / "src"), str(Path(__file__).resolve().parent)]
    from AuditStockSketchProjection import require, source_fingerprint

    if args.worker:
        case, mode = args.worker
        require(mode in ("path", "bytes"), "unknown cut read transport")
        print(json.dumps(worker(root, case, mode), sort_keys=True))
        return
    fingerprint = source_fingerprint(repository)
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {
            (case, mode): executor.submit(
                run,
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).resolve()),
                    str(repository),
                    str(root),
                    str(args.output),
                    "--worker",
                    case,
                    mode,
                ],
                text=True,
                capture_output=True,
                timeout=60,
            )
            for case in CASES
            for mode in ("path", "bytes")
        }
        for key, job in jobs.items():
            outcome = job.result()
            require(outcome.returncode == 0, outcome.stderr)
            results[key] = json.loads(outcome.stdout)
    for case in CASES:
        require(
            results[case, "path"] == results[case, "bytes"],
            "path and byte cut reads differ",
        )
    require(
        fingerprint == source_fingerprint(repository),
        "sdk source changed during the audit",
    )
    report = {
        "schema": "kit.sw2026.cold-through-all-geometry-read.v1",
        "passed": True,
        "source_fingerprint": fingerprint,
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": {case: results[case, "path"] for case in CASES},
        "sdk_processes": len(results),
        "heldout_inputs_read": 0,
        "native_processes_started": 0,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
