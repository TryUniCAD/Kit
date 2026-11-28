from __future__ import annotations

import argparse
from collections import Counter
import json
from math import isclose
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

import AuthorCurves as curves
from InspectDrawingCache import drawing_tree
from InspectFrontDrawingMap import phase

SCHEMA = "kit.sw2026.original-drawing-partial-native-geometry.v1"
TOOLS = (
    "AuthorCurves.py",
    "AuthorDrawingSources.py",
    "DrawingCacheCases.py",
    "InspectDrawingCache.py",
    "InspectFrontDrawingMap.py",
    "OracleIdentity.py",
    "Swapp.py",
    "InspectOriginalDrawingGeometry.py",
)
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
WRITER = "645a423b76792abc04823cdf44a72c3df940847d1e4bd966dc07e6b57ea3d864"


def checked(root, name, expected):
    target = (root / name).resolve(strict=True)
    curves.require(
        target.is_relative_to(root)
        and target.is_file()
        and curves.digest(target) == expected,
        "partial geometry packet evidence changed: " + name,
    )
    return target


def verify(packet, packet_sha):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, packet_sha).read_bytes())
    curves.require(
        job["schema"] == SCHEMA
        and job["oracle_sha256"] == ORACLE
        and job["writer_manifest_sha256"] == WRITER,
        "partial geometry packet identity differs",
    )
    curves.require(
        job["complete_source_admitted"] is False
        and job["source_semantics_passed"] is False
        and job["heldout_acceptance"] is False
        and job["partial_geometry_only"] is True,
        "this packet cannot claim original source semantic acceptance",
    )
    curves.require(
        [row["name"] for row in job["cases"]] == ["H01SheetA", "H02SheetB"]
        and job["expected_fresh_processes"] == 12,
        "partial geometry case or process inventory changed",
    )
    tools = (root / "Tools").resolve(strict=True)
    curves.require(
        Path(__file__).resolve().parent == tools
        and set(job["tools_sha256"]) == set(TOOLS),
        "partial geometry observer closure differs",
    )
    for name, sha in job["tools_sha256"].items():
        checked(tools, name, sha)
    for row in job["evidence_files"]:
        checked(root, row["path"], row["sha256"])
    for row in [
        job["control"],
        *[
            value
            for case in job["cases"]
            for value in (case["original"], case["generated"])
        ],
    ]:
        for kind in ("drawing", "part"):
            value = row[kind]
            path = checked(root, value["path"], value["sha256"])
            curves.require(
                path.stat().st_size == value["bytes"],
                "partial geometry input size changed",
            )
        curves.require(
            row["expected"]["view"]["configuration"] == "authored configuration"
            and row["expected"]["view"]["child_volume_m3"] > 0,
            "partial native expectations are incomplete",
        )
    target_root = PureWindowsPath(job["generated_windows_root"])
    targets = []
    for case in job["cases"]:
        for kind in ("drawing", "part"):
            value = case["generated"][kind]
            target = PureWindowsPath(value["encoded_windows_path"])
            curves.require(
                target.is_absolute()
                and target.is_relative_to(target_root)
                and target.name == Path(value["path"]).name,
                "generated linked locator changed",
            )
            targets.append(str(target))
    curves.require(len(set(targets)) == 4, "generated paths are not unique")
    return job


def same_path(actual, expected):
    left, right = Path(actual).resolve(), Path(expected).resolve()
    return left == right or left.is_file() and right.is_file() and left.samefile(right)


def close_line(author, actual, expected):
    candidates = list(actual)
    curves.require(
        len(candidates) == len(expected) == 4,
        "linked child lost four actual sketch segments",
    )
    for index, (start, end) in enumerate(expected):
        match = None
        for number, item in enumerate(candidates):
            if item["kind"] != "line" or item["construction"]:
                continue
            values = [*item["start"], *item["end"]]
            target = [*start, *end]
            if all(
                isclose(a, b, rel_tol=2e-7, abs_tol=1e-10)
                for a, b in zip(values, target, strict=True)
            ):
                match = number
                break
        curves.require(
            match is not None, "linked child line endpoints differ from source geometry"
        )
        item = candidates.pop(match)
        for label in ("start", "end"):
            target = start if label == "start" else end
            for axis, value in enumerate(item[label]):
                author.rec.close_number(
                    f"linked line {index} {label} {axis}",
                    value,
                    target[axis],
                    absolute=1e-10,
                )


def observe_link(author, drawing, native, row, wanted):
    curves.require(
        same_path(author.get(author.model, "GetPathName"), native),
        "drawing opened a different input",
    )
    sentinel = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sentinel, "GetNextView"), "View")
    child = author.get(view, "ReferencedDocument")
    actual = Path(author.get(child, "GetPathName")).resolve()
    allowed = [wanted]
    if row["role"] != "generated":
        allowed.append(Path(row["original_reference_path"]))
    curves.require(
        any(same_path(actual, value) for value in allowed)
        and curves.digest(actual) == row["part"]["sha256"],
        "drawing did not resolve one of its exact declared child identities",
    )
    if row["role"] == "generated":
        curves.require(
            same_path(actual, wanted),
            "generated drawing used a native original reference",
        )
    native_drawing_tree = drawing_tree(author)
    original_model, original_sketch = author.model, author.sketch
    try:
        author.model = child
        part = author.typed(child, "PartDoc")
        body_count = len(author.get(part, "GetBodies2", 0, False) or ())
        curves.require(
            body_count == 1,
            "linked child must contain exactly one solid body including hidden bodies",
        )
        native_child_tree = drawing_tree(author)
        feature_states = author.rec.call(
            "read complete linked child top-level states", author.sw.features, child
        )
        curves.require(
            all(
                item.get("error") == 0
                and item.get("warning") is False
                and item.get("suppressed") is False
                for item in feature_states
            ),
            "linked child has feature errors warnings suppression or incomplete state",
        )
        problems = int(author.get(author.get(child, "Extension"), "GetWhatsWrongCount"))
        curves.require(problems == 0, "linked child has native problems")
        feature = author.get(child, "FeatureByName", row["sketch_name"])
        author.sketch = author.typed(
            author.get(feature, "GetSpecificFeature2"), "Sketch"
        )
        geometry = author.geometry()
        vertices = row["vertices_m"]
        close_line(
            author,
            geometry,
            [(vertices[index], vertices[(index + 1) % 4]) for index in range(4)],
        )
        parameter_name = "D1@" + row["boss_name"]
        dimension = author.get(child, "Parameter", parameter_name)
        curves.require(
            dimension is not None
            and author.get(dimension, "DrivenState") == 2
            and not bool(author.get(dimension, "ReadOnly")),
            "linked child lost its actual editable driving depth",
        )
        value = float(author.get(dimension, "SystemValue"))
        author.rec.close_number("linked actual D1 depth", value, row["depth_m"])
        parents = {}
        for name in (row["sketch_name"], row["boss_name"]):
            feature = author.get(child, "FeatureByName", name)
            parents[name] = [
                str(author.get(item, "Name"))
                for item in author.get(feature, "GetParents") or ()
            ]
        curves.require(
            parents
            == {
                row["sketch_name"]: [row["support_name"]],
                row["boss_name"]: [row["sketch_name"], row["support_name"]],
            },
            "linked child profile or From-support dependencies differ",
        )
        return {
            "resolved_child_path": str(actual),
            "resolved_child_sha256": curves.digest(actual),
            "referenced_configuration": str(
                author.get(view, "ReferencedConfiguration")
            ),
            "view_reference_name": str(author.get(view, "GetReferencedModelName")),
            "drawing_tree": native_drawing_tree,
            "child_tree": native_child_tree,
            "child_feature_states": feature_states,
            "child_solid_body_count": body_count,
            "child_whats_wrong": problems,
            "child_geometry": geometry,
            "driving_parameter": {
                "query": parameter_name,
                "value_m": value,
                "driven_state": 2,
                "read_only": False,
            },
            "feature_parents": parents,
            "partial_source_projection": True,
        }
    finally:
        author.model, author.sketch = original_model, original_sketch


def tree_difference(source, generated):
    left = Counter(tuple(row) for row in source)
    right = Counter(tuple(row) for row in generated)
    return {
        "equal_in_exact_order": source == generated,
        "source_count": len(source),
        "generated_count": len(generated),
        "source_only_rows": [list(row) for row in (left - right).elements()],
        "generated_only_rows": [list(row) for row in (right - left).elements()],
        "source_rows": source,
        "generated_rows": generated,
    }


def run(packet, packet_sha):
    curves.require(
        os.name == "nt",
        "native geometry execution belongs to the root-owned Windows oracle",
    )
    job = verify(packet, packet_sha)
    root = packet.parent.resolve(strict=True)
    output = root / "Inspection"
    curves.require(not output.exists(), "native result directory must be unused")
    for case in job["cases"]:
        for kind in ("drawing", "part"):
            curves.require(
                not Path(case["generated"][kind]["encoded_windows_path"]).exists(),
                "generated guest path already exists; never overwrite a prior input",
            )
    import Swapp
    from OracleIdentity import application_identity

    output.mkdir()
    result = {
        "schema": SCHEMA,
        "packet_sha256": packet_sha,
        "phases": {},
        "comparisons": [],
        "partial_geometry_only": True,
        "source_semantics_passed": False,
        "complete_source_admitted": False,
        "heldout_acceptance": False,
        "native_acceptance": False,
        "geometry_qualified": False,
        "writer_manifest_sha256": WRITER,
        "heldout_originals_exposed": 2,
        "observer_contains_no_runtime_hooks": True,
        "public_writer_admission_changed": False,
    }
    stages = result["phases"]

    def checkpoint():
        curves.write_json(output / "Result.json", result)

    def measure(label, row, tree=None):
        native = (
            Path(row["drawing"]["encoded_windows_path"])
            if row["role"] == "generated"
            else root / row["drawing"]["path"]
        )
        wanted = (
            Path(row["part"]["encoded_windows_path"])
            if row["role"] == "generated"
            else root / row["part"]["path"]
        )
        expected = row["expected"]
        original_reference = (
            str(wanted)
            if row["role"] == "generated"
            else row["original_reference_path"]
        )

        def observe(author, drawing, opened):
            return observe_link(author, drawing, opened, row, wanted)

        common = {
            "child": wanted,
            "original_child": original_reference,
            "child_hash": row["part"]["sha256"],
            "oracle": ORACLE,
            "observe": observe,
        }
        first = phase(
            Swapp,
            application_identity,
            directory=output / label / "OpenEditSave",
            native=native,
            sha256=row["drawing"]["sha256"],
            expected=expected,
            tree=tree,
            edit=True,
            **common,
        )
        stages[label + "/OpenEditSave"] = first
        checkpoint()
        if not first["passed"]:
            return first, False
        reopened = phase(
            Swapp,
            application_identity,
            directory=output / label / "FreshReopen",
            native=output / label / "OpenEditSave/EditedDrawing.SLDDRW",
            sha256=first["derivative_sha256"],
            expected=first["edited"],
            tree=first["tree"],
            edit=False,
            **common,
        )
        stages[label + "/FreshReopen"] = reopened
        checkpoint()
        return first, reopened["passed"]

    control_before = None
    healthy_before = False
    candidates = True
    try:
        control_before, healthy_before = measure("ControlBefore", job["control"])
        if healthy_before:
            for case in job["cases"]:
                for kind in ("drawing", "part"):
                    row = case["generated"][kind]
                    target = Path(row["encoded_windows_path"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with (root / row["path"]).open("rb") as source, target.open(
                        "xb"
                    ) as destination:
                        copyfileobj(source, destination)
                    curves.require(
                        curves.digest(target) == row["sha256"],
                        "staged generated bytes changed",
                    )
                original, source_pass = measure(
                    case["name"] + "/Original", case["original"]
                )
                generated, output_pass = measure(
                    case["name"] + "/Generated", case["generated"]
                )
                candidates = candidates and source_pass and output_pass
                if original.get("initial_link") and generated.get("initial_link"):
                    left, right = original["initial_link"], generated["initial_link"]
                    result["comparisons"].append(
                        {
                            "case": case["name"],
                            "source_semantics_passed": False,
                            "drawing_tree": tree_difference(
                                left["drawing_tree"], right["drawing_tree"]
                            ),
                            "child_tree": tree_difference(
                                left["child_tree"], right["child_tree"]
                            ),
                            "source_child_path": left["resolved_child_path"],
                            "generated_child_path": right["resolved_child_path"],
                            "source_reference_name": left["view_reference_name"],
                            "generated_reference_name": right["view_reference_name"],
                            "reference_paths_intentionally_differ": True,
                            "configuration_equal": left["referenced_configuration"]
                            == right["referenced_configuration"],
                            "driving_parameter": {
                                "source": left["driving_parameter"],
                                "generated": right["driving_parameter"],
                            },
                            "retained_original_unsupported": case["unsupported"],
                        }
                    )
                    checkpoint()
    except Exception as error:
        result["error"] = repr(error)
    finally:
        healthy_after = False
        try:
            _, healthy_after = measure(
                "ControlAfter",
                job["control"],
                control_before.get("tree") if healthy_before else None,
            )
        except Exception as error:
            result["control_after_error"] = repr(error)
        try:
            terminal = verify(packet, packet_sha)
            immutable = terminal == job
        except Exception as error:
            result["final_packet_verification_error"] = repr(error)
            immutable = False
        starts = [
            row["oracle_identity"]["process_creation_filetime"]
            for row in stages.values()
            if row.get("oracle_identity")
        ]
        for case in job["cases"]:
            for kind in ("drawing", "part"):
                row = case["generated"][kind]
                path = Path(row["encoded_windows_path"])
                immutable = (
                    immutable
                    and path.is_file()
                    and curves.digest(path) == row["sha256"]
                )
        result.update(
            controls_healthy=healthy_before and healthy_after,
            native_inputs_immutable=immutable,
            distinct_processes=len(set(starts)),
            completed_phases=len(stages),
        )
        result["geometry_qualified"] = bool(
            result["controls_healthy"]
            and candidates
            and immutable
            and len(stages) == len(set(starts)) == 12
            and len(result["comparisons"]) == 2
            and all(row["passed"] for row in stages.values())
        )
        result["semantic_tree_equality"] = bool(
            len(result["comparisons"]) == 2
            and all(
                row["drawing_tree"]["equal_in_exact_order"]
                and row["child_tree"]["equal_in_exact_order"]
                for row in result["comparisons"]
            )
        )
        result["child_driving_edit_performed"] = False
        result["full_parametric_bundle_qualification"] = False
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Compare explicitly partial generated geometry against two exact original drawings without claiming semantic acceptance"
    )
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        print(
            '{"verified":true,"native_execution":false,"source_semantics_passed":false}'
        )
        return 0
    result = run(packet, args.packet_sha256)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "geometry_qualified",
                    "source_semantics_passed",
                    "heldout_acceptance",
                    "distinct_processes",
                )
            }
        )
    )
    return 0 if result["geometry_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
