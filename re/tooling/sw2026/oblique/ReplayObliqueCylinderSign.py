import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys

from ObliqueCylinderPlan import angle_arguments, cases as old_cases
from ObliqueFlipPlan import (
    BASES,
    NAMES,
    ORDERED_HINGE_PLANES,
    PLANE_NORMALS,
    cases,
    cross,
    dot,
    prediction,
    require,
    rotate,
    unit,
)

SOURCE_SHA256 = "a37ee38c396be766b8de364994d6d21913087b1372b6cf41249fedc1fc5e3c3a"
STATIC_SHA256 = "023381546a7e9bed481309fc17274daf80a6f3f9cf5b9161c489fbe126c22364"


def checked(path, expected):
    require(
        path.is_file()
        and not path.is_symlink()
        and sha256(path.read_bytes()).hexdigest() == expected,
        "declared disclosed evidence identity differs",
    )
    return json.loads(path.read_bytes())


def canonical(value):
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def replay(disclosed, static):
    source = checked(disclosed, SOURCE_SHA256)
    pin = checked(static, STATIC_SHA256)
    require(
        pin["function_count"] == 16 and pin["native_launches"] == 0,
        "native pin scope differs",
    )
    snapshot = source["partial_oblique_snapshot"]
    require(
        "mass" not in snapshot, "do not silently extend the failed observation scope"
    )
    original = old_cases()[0]
    rows = {}
    for suffix in ("a", "b"):
        hinge_key, plane_key = "hinge_" + suffix, "angle_" + suffix
        parents = [value["name"] for value in snapshot["parents"][hinge_key]]
        names = [name.title() + " Plane" for name in ORDERED_HINGE_PLANES[hinge_key]]
        require(parents == names, "actual ordered hinge owners differ")
        first, second = ORDERED_HINGE_PLANES[hinge_key]
        direction = unit(cross(PLANE_NORMALS[first], PLANE_NORMALS[second]))
        observed_direction = snapshot["axes"][hinge_key]["unit"]
        require(
            all(
                isclose(a, b, abs_tol=1e-14)
                for a, b in zip(direction, observed_direction, strict=True)
            ),
            "actual directed hinge differs from ordered owner normals",
        )
        arguments = angle_arguments(original[plane_key + "_rad"])
        angle = -arguments[1] if arguments[0] & 256 else arguments[1]
        normal = rotate(BASES[plane_key], direction, angle)
        observed_normal = snapshot["planes"][plane_key]["normal"]
        require(
            all(
                isclose(a, b, abs_tol=1e-14)
                for a, b in zip(normal, observed_normal, strict=True)
            ),
            "source normal does not follow the independently derived directed rotation",
        )
        prior = snapshot["expected_geometry"]["angle_plane_normals"][plane_key]
        disagreement = [a - b for a, b in zip(observed_normal, prior, strict=True)]
        require(
            max(map(abs, disagreement)) > 0.1,
            "original incorrect prediction was not retained",
        )
        rows[plane_key] = {
            "ordered_hinge_parent_names": parents,
            "observed_directed_hinge": observed_direction,
            "constructed_directed_hinge": direction,
            "actual_input_arguments": arguments,
            "observed_normal": observed_normal,
            "independently_rotated_normal": normal,
            "max_normal_residual": max(
                abs(a - b) for a, b in zip(normal, observed_normal, strict=True)
            ),
            "preserved_original_predicted_normal": prior,
            "observed_minus_original_prediction": disagreement,
        }
    observed_axis = snapshot["axes"]["direction"]["unit"]
    calculated_axis = unit(
        cross(
            snapshot["planes"]["angle_b"]["normal"],
            snapshot["planes"]["angle_a"]["normal"],
        )
    )
    require(
        all(
            isclose(a, b, abs_tol=1e-14)
            for a, b in zip(observed_axis, calculated_axis, strict=True)
        ),
        "actual final axis differs from the two ordered angle-plane normals",
    )
    fresh = {
        case["id"]: {str(index): prediction(case, index) for index in range(5)}
        for case in cases()
    }
    require(
        all(
            row["reverse"]
            for state in fresh["F01"].values()
            for row in state["angle_input_plans"].values()
        )
        and not any(
            row["reverse"]
            for state in fresh["F02"].values()
            for row in state["angle_input_plans"].values()
        ),
        "the independent pair does not span both flip states",
    )
    return {
        "schema": "kit.sw2026.oblique-cylinder-sign-replay.v1",
        "passed": True,
        "disclosed_author_sha256": SOURCE_SHA256,
        "static_pin_sha256": STATIC_SHA256,
        "native_partial_rows": rows,
        "observed_final_axis": observed_axis,
        "ordered_plane_cross_axis": calculated_axis,
        "native_driver_owners": {
            key: NAMES[key] for key in ("angle_a", "angle_b", "limit", "sketch")
        },
        "new_independent_prediction_sha256": canonical(fresh),
        "new_independent_case_count": 2,
        "new_independent_state_count": 10,
        "new_native_execution_attempted": False,
        "original_source_save_measured": False,
        "original_geometry_acceptance": False,
        "writer_output_count": 0,
        "heldout_reads": 0,
    }


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--disclosed-author", type=Path, required=True)
    parser.add_argument("--static-pin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        not args.output.exists() and args.output.parent.is_dir(),
        "choose unused replay output",
    )
    result = replay(args.disclosed_author, args.static_pin)
    args.output.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "passed": True,
                "output_sha256": sha256(args.output.read_bytes()).hexdigest(),
                "independent_states": result["new_independent_state_count"],
                "native_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
