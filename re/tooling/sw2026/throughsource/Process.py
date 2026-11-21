import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys


def brep_observation(document, shape, prediction):
    if document.brep is None:
        return {"available": False, "reason": "not used as a prediction input"}
    points = tuple(
        (value.point.x * 0.001, value.point.y * 0.001, value.point.z * 0.001)
        for value in document.brep.vertices
    )
    minimum = tuple(min(point[index] for point in points) for index in range(3))
    maximum = tuple(max(point[index] for point in points) for index in range(3))
    from interchange.brep.Curves.BrepCurves import CircleCurve

    centers = tuple(
        sorted(
            (value.center.x * 0.001, value.center.y * 0.001, value.center.z * 0.001)
            for value in document.brep.curves
            if isinstance(value, CircleCurve)
        )
    )
    expected = tuple(sorted(prediction["rim_centers_world_m"]))
    close = lambda a, b: all(
        isclose(x, y, rel_tol=1e-10, abs_tol=1e-12) for x, y in zip(a, b, strict=True)
    )
    bounds_equal = close(minimum, prediction["bounds_m"]["minimum"]) and close(
        maximum, prediction["bounds_m"]["maximum"]
    )
    rims_equal = len(centers) == len(expected) and all(
        close(a, b) for a, b in zip(centers, expected)
    )
    counts = {
        "face_count": len(document.brep.faces),
        "edge_count": len(document.brep.edges),
        "vertex_count": len(document.brep.vertices),
    }
    count_equal = all(counts[key] == prediction[key] for key in counts)
    if not (bounds_equal and rims_equal and count_equal):
        raise ValueError(
            "actual independent source BRep disagrees with analytic portable prediction"
        )
    return {
        "available": True,
        "prediction_frozen_before_brep_inspection": True,
        "brep_is_generation_input": False,
        "bounds_m": {"minimum": minimum, "maximum": maximum},
        "rim_centers_world_m": centers,
        "topology_counts": counts,
        "bounds_equal": bounds_equal,
        "signed_rims_equal": rims_equal,
        "counts_equal": count_equal,
        "source_fallback_body_bounds_trusted": False,
    }


def audit(document, output, edited_depth):
    from Coverage import canonical, normalize, require_qualified
    from Predict import predict
    from Shape import read_shape

    shape = read_shape(document)
    prediction = predict(shape)
    normalized, coverage = normalize(document, shape)
    output.mkdir(parents=True, exist_ok=False)
    write = lambda name, data: (output / name).write_bytes(canonical(data) + b"\n")
    write("Prediction.json", prediction)
    if edited_depth is not None:
        write("EditedPrediction.json", predict(shape, edited_depth))
    write("Shape.json", shape)
    write("NormalizedDocument.json", normalized.to_dict())
    write("Coverage.json", coverage)
    observation = brep_observation(document, shape, prediction)
    write("IndependentBrepObservation.json", observation)
    try:
        require_qualified(coverage)
    except ValueError as error:
        admission = {"refused": True, "reason": str(error)}
    else:
        raise ValueError("unqualified source unexpectedly reached acceptance")
    receipt = {
        "source_sha256": document.source.sha256,
        "source_owner_ids_preserved": coverage["source_owner_ids_preserved"],
        "source_native_bytes_in_normalized_document": coverage[
            "source_native_bytes_in_normalized_document"
        ],
        "shape_projection_passed": True,
        "source_equivalence_gate": admission,
        "native_acceptance": False,
        "held_out_accessed": False,
        "oracle_used": False,
        "files_sha256": {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted(output.iterdir())
            if path.is_file()
        },
    }
    write("Result.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edited-depth-m", type=float)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.root / "src"))
    from interchange import CadDocument

    data = json.load(sys.stdin)
    if args.compare:
        from Compare import compare

        source = CadDocument.from_dict(data["source"])
        candidate = CadDocument.from_dict(data["candidate"])
        result = compare(source, candidate)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "Result.json").write_text(json.dumps(result, indent=2) + "\n")
    else:
        result = audit(CadDocument.from_dict(data), args.output, args.edited_depth_m)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
