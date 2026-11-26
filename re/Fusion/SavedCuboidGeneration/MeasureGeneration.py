import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isclose, isfinite
import os
from pathlib import Path
import runpy
from time import perf_counter_ns
from traceback import format_exc


STAGES = ("ControlBefore", "Candidate", "Reopen", "ControlAfter")
AXES = ("width", "depth", "height")
ROOT = Path(__file__).resolve().parent
FILES = {
    "author": ROOT / "AuthorGenerationControl.py",
    "geometry": ROOT.parent / "LocalOracle/EncoderRoundTrip/Measure.py",
    "presentation": ROOT.parent / "SavedCuboidWriter/ObservePresentation.py",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def utc():
    return datetime.now(timezone.utc).isoformat()


def prepare(source, output):
    source, output = source.resolve(), output.resolve()
    request_path = source / "Request.json"
    candidate_path = source / "Candidate.f3d"
    pending_path = source / "NativePending.json"
    pending = json.loads(pending_path.read_bytes())
    edits_path = source / "RunParameters.json"
    edits = json.loads(edits_path.read_bytes())
    request = json.loads(request_path.read_bytes())
    runner_sha = digest(Path(__file__))
    expected_driver_edits = {axis: edits[f"native_{axis}_edit_mm"] for axis in AXES}
    require(pending["status"] == "native_unmeasured" and digest(request_path) == pending["request_sha256"] == edits["request_sha256"]
            and digest(candidate_path) == pending["candidate_sha256"], "Oracle staging digests differ")
    require(digest(FILES["author"]) == pending["author_control_sha256"], "Pinned control helper changed")
    require(edits.get("edit_mm", expected_driver_edits) == expected_driver_edits
            and pending.get("edit_mm", expected_driver_edits) == expected_driver_edits
            and all(isfinite(value) and value > 0 and value != request["dimensions_mm"][axis]
                    for axis, value in expected_driver_edits.items()), "Missing or inconsistent exact driver edits")
    output.mkdir()
    batch = output / "Batch.json"
    batch.write_text(json.dumps({
        "case": pending["case"], "sdk_revision": pending["sdk_revision"], "producer_sha256": pending["producer_sha256"],
        "written_at": pending["written_at"], "request": str(request_path), "request_sha256": digest(request_path),
        "candidate": str(candidate_path), "candidate_sha256": digest(candidate_path), "pending_sha256": digest(pending_path),
        "edit_mm": expected_driver_edits, "runner_sha256": runner_sha,
        "helpers": {role: {"path": str(path), "sha256": digest(path)} for role, path in FILES.items()},
    }, indent=2) + "\n", encoding="utf-8")
    batch_sha = digest(batch)
    for stage in STAGES:
        folder = output / stage
        folder.mkdir()
        (folder / f"{stage}.py").write_text(
            "from hashlib import sha256\nfrom pathlib import Path\nimport runpy\n"
            f"script = Path({str(Path(__file__).resolve())!r})\n"
            f"if sha256(script.read_bytes()).hexdigest() != {runner_sha!r}:\n"
            "    raise RuntimeError('Pinned generation oracle changed')\n"
            f"runpy.run_path(str(script))['measure'](Path({str(batch)!r}), {batch_sha!r}, {stage!r})\n",
            encoding="utf-8",
        )
    return batch_sha


def projected_shape(state, request):
    aliases = dict(zip((request["drivers"][axis] for axis in AXES), ("kitWidth", "kitDepth", "kitHeight"), strict=True))
    return {
        **state,
        "timeline": [
            {**state["timeline"][0], "name": "Encoder Rectangle"},
            {**state["timeline"][1], "name": "Encoder Extrusion"},
        ],
        "sketches": [{**state["sketches"][0], "dimensions": sorted(aliases[name] for name in state["sketches"][0]["dimensions"])}],
        "bodies": [{**state["bodies"][0], "name": "Encoder Cuboid"}],
        "user_parameters": {aliases[name]: value for name, value in state["user_parameters"].items()},
        "model_parameters": [
            {**row, "expression": aliases.get(row["expression"], row["expression"])} for row in state["model_parameters"]
        ],
    }


def check_native_graph(design, request, size):
    import adsk.fusion

    root = design.rootComponent
    sketch = root.sketches.item(0)
    require(sketch.referencePlane == root.xYConstructionPlane, "Sketch reference is not the root XY plane")
    origin = sketch.originPoint
    corners = [point for point in sketch.sketchPoints if point != origin]
    fixed = [point for point in corners if point.isFixed]
    require(len(corners) == 4 and len(fixed) == 1 and origin.isFixed and tuple(fixed[0].geometry.asArray()) == (0, 0, 0),
            "Sketch origin and anchored corner differ")
    anchor = fixed[0]
    orientations = adsk.fusion.DimensionOrientations
    rows = {}
    for dimension in sketch.sketchDimensions:
        linear = adsk.fusion.SketchLinearDimension.cast(dimension)
        name = dimension.parameter.expression
        role = next((axis for axis in AXES[:2] if request["drivers"][axis] == name), None)
        require(role is not None and role not in rows and linear and linear.isDriving, "Unexpected sketch driver")
        expected_orientation = (orientations.HorizontalDimensionOrientation if role == "width"
                                else orientations.VerticalDimensionOrientation)
        first = adsk.fusion.SketchPoint.cast(linear.entityOne)
        second = adsk.fusion.SketchPoint.cast(linear.entityTwo)
        require(first and second and ((first == anchor) != (second == anchor))
                and linear.orientation == expected_orientation, "Wrong anchored dimension operands")
        other = second if first == anchor else first
        expected = (size[role] / 10, 0, 0) if role == "width" else (0, size[role] / 10, 0)
        require(other in corners and all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8)
                for a, b in zip(other.geometry.asArray(), expected, strict=True))
                and isclose(linear.value, size[role] / 10, rel_tol=1e-8), "Dimension value or endpoint differs")
        rows[role] = {"parameter": dimension.parameter.name, "expression": name, "value_cm": linear.value,
                      "operands_cm": [first.geometry.asArray(), second.geometry.asArray()],
                      "caption_cm": linear.textPosition.asArray(), "orientation": int(linear.orientation)}
    require(rows.keys() == {"width", "depth"}, "Two independent driving dimensions required")
    extrude = root.features.extrudeFeatures.item(0)
    extent = adsk.fusion.DistanceExtentDefinition.cast(extrude.extentOne)
    require(extrude.operation == adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            and extrude.symmetricExtent is None and not extrude.hasTwoExtents and extent
            and extent.distance.expression == request["drivers"]["height"]
            and isclose(extent.distance.value, size["height"] / 10, rel_tol=1e-8)
            and extrude.bodies.count == 1 and extrude.bodies.item(0) == root.bRepBodies.item(0),
            "Extrusion does not own the expected one-sided driven solid")
    return {"anchored_corner_cm": anchor.geometry.asArray(), "distinct_sketch_origin_cm": origin.geometry.asArray(),
            "sketch_dimensions": rows,
            "extrude_extent": {"parameter": extent.distance.name, "expression": extent.distance.expression,
                               "value_cm": extent.distance.value, "operation": int(extrude.operation)}}


def measure(batch_path, expected_batch_sha, stage):
    import adsk.core
    import adsk.fusion

    require(stage in STAGES and digest(batch_path) == expected_batch_sha, "Fusion generation batch changed")
    batch = json.loads(batch_path.read_bytes())
    require(digest(Path(__file__)) == batch["runner_sha256"], "Generation runner changed")
    request_path, candidate = Path(batch["request"]), Path(batch["candidate"])
    request = json.loads(request_path.read_bytes())
    require(digest(request_path) == batch["request_sha256"] and digest(candidate) == batch["candidate_sha256"],
            "Request or candidate changed after prepare")
    helpers = {}
    for role, pin in batch["helpers"].items():
        path = Path(pin["path"])
        require(digest(path) == pin["sha256"], f"Pinned {role} helper changed")
        helpers[role] = runpy.run_path(str(path))
    geometry, presentation = helpers["geometry"], helpers["presentation"]
    app = adsk.core.Application.get()
    root = batch_path.parent
    receipt = root / f"{stage}.json"
    require(not receipt.exists(), "Use a fresh stage receipt path")
    control, edited, restored = (root / f"{name}.f3d" for name in ("VendorControl", "VendorEdited", "VendorRestored"))
    report = {"stage": stage, "case": batch["case"], "pid": os.getpid(), "fusion_version": app.version,
              "started_utc": utc(), "documents_before": app.documents.count, "status": "running",
              "batch_sha256": expected_batch_sha, "runner_sha256": batch["runner_sha256"],
              "request_sha256": batch["request_sha256"], "candidate_sha256": batch["candidate_sha256"],
              "measurements": {}, "archives": {}, "presentation_errors": {},
              "pending": ["native dialog watch", "strict SDK readback after native save", "viewport and archived previews"]}
    started = perf_counter_ns()
    document = None

    def checkpoint():
        temporary = receipt.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(receipt)

    def open_archive(path, wanted):
        nonlocal document
        require(document is None and digest(path) == wanted, f"Unexpected bytes or prior document at {path.name}")
        report["archives"][path.name] = wanted
        report["last_operation"] = f"open {path.name}"
        checkpoint()
        options = app.importManager.createFusionArchiveImportOptions(str(path))
        document = app.importManager.importToNewDocument(options)
        return geometry["design_for"](document)

    def close_document():
        nonlocal document
        if document is not None:
            require(document.close(False), "Could not close the task-owned document")
            document = None

    def save(design, path):
        report["last_operation"] = f"local export {path.name}"
        checkpoint()
        report["archives"][path.name] = geometry["export"](design, path)

    def check(label, design, size, rebuild=False):
        report["last_operation"] = label
        checkpoint()
        if rebuild:
            require(design.computeAll(), "Fusion could not rebuild")
        state = geometry["observe"](design)
        report["measurements"][label] = state
        names = request["names"]
        require(len(state["timeline"]) == 2 and len(state["bodies"]) == len(state["sketches"]) == 1
                and [node["name"] for node in state["timeline"]] == [names["sketch"], names["extrude"]]
                and state["bodies"][0]["name"] == names["body"] and state["sketches"][0]["name"] == names["sketch"],
                "Observed history or body names differ")
        require(set(state["user_parameters"]) == set(request["drivers"].values()), "Driver roster differs")
        geometry["require_shape"](projected_shape(state, request), *(size[axis] for axis in AXES), True)
        state["native_graph"] = check_native_graph(design, request, size)
        target = request["material"]
        native_body = design.rootComponent.bRepBodies.item(0)
        body = state["bodies"][0]
        density = target["density_kg_m3"] / 1_000_000
        require(body["material"] == target["label"] and isclose(body["density_kg_per_cm3"], density, rel_tol=1e-8)
                and isclose(body["mass_kg"], density * body["volume_cm3"], rel_tol=1e-8),
                "Requested physical material or measured mass differs")
        material = native_body.material
        appearance = native_body.appearance
        state["material_bindings"] = {"physical_id": material.id, "effective_appearance_id": appearance.id,
                                      "associated_appearance_id": material.appearance.id,
                                      "source_type": int(native_body.appearanceSourceType)}
        try:
            color = appearance.color
            state["material_bindings"]["rgba8"] = [color.red, color.green, color.blue, color.opacity]
            state["presentation"] = presentation["observe_loaded_presentation"](app.activeViewport, design)
        except (AttributeError, RuntimeError) as error:
            report["presentation_errors"][label] = str(error)
        rgba = state["material_bindings"].get("rgba8")
        if rgba is not None:
            require(rgba == [round(value * 255) for value in target["rgba"]], "Requested effective RGBA differs")
        checkpoint()

    size = request["dimensions_mm"]
    for_edit = {**size, "height": batch["edit_mm"]["height"]}

    def exercise(design, axis, capture=None):
        param = design.userParameters.itemByName(request["drivers"][axis])
        before = param.expression
        param.expression = f"{batch['edit_mm'][axis]} mm"
        check(f"{axis}_edited", design, {**size, axis: batch["edit_mm"][axis]}, True)
        if capture:
            save(design, capture)
        param.expression = before
        check(f"{axis}_restored", design, size, True)

    try:
        checkpoint()
        require(app.documents.count == 0, "Generation oracle requires zero open documents")
        previous = {}
        for earlier in STAGES[:STAGES.index(stage)]:
            path = root / f"{earlier}.json"
            if stage == "ControlAfter" and earlier in ("Candidate", "Reopen") and not path.exists():
                continue
            data = json.loads(path.read_bytes())
            require(data["batch_sha256"] == expected_batch_sha and data["fusion_version"] == app.version
                    and data["documents_after"] == data["documents_before"] == 0 and data["pid"] != report["pid"]
                    and all(data["pid"] != item["pid"] for item in previous.values()),
                    "Earlier receipt has inconsistent batch, build, process, or cleanup")
            previous[earlier] = data
        if stage == "ControlBefore":
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design, report["control_authoring"] = helpers["author"]["author_control"](document, request)
            check("authored", design, size)
            save(design, control)
            close_document()
            design = open_archive(control, report["archives"][control.name])
            check("opened", design, size)
            check("rebuilt", design, size, True)
            exercise(design, "height")
        elif stage == "Candidate":
            require(previous["ControlBefore"]["status"] == "passed", "Starting control is unhealthy")
            design = open_archive(candidate, batch["candidate_sha256"])
            check("opened", design, size)
            check("rebuilt", design, size, True)
            design.timeline.markerPosition = 1
            root_component = design.rootComponent
            require(root_component.bRepBodies.count == 0 and root_component.sketches.count == 1,
                    "Timeline rollback did not retain only the sketch")
            require(design.timeline.moveToEnd(), "Timeline restore failed")
            check("rolled_forward", design, size, True)
            exercise(design, "height", edited)
            save(design, restored)
            exercise(design, "width")
            exercise(design, "depth")
        elif stage == "Reopen":
            require(previous["Candidate"]["status"] == "passed", "Candidate did not measure successfully")
            for label, path, dimensions in (("edited", edited, for_edit), ("restored", restored, size)):
                design = open_archive(path, previous["Candidate"]["archives"][path.name])
                check(f"{label}_opened", design, dimensions)
                check(f"{label}_rebuilt", design, dimensions, True)
                close_document()
        else:
            require(previous["ControlBefore"]["status"] == "passed", "Starting control is unhealthy")
            design = open_archive(control, previous["ControlBefore"]["archives"][control.name])
            check("opened", design, size)
            check("rebuilt", design, size, True)
            exercise(design, "height")
            report["bracket_status"] = ("geometry_material_lifecycle_measured"
                                        if all(previous.get(name, {}).get("status") == "passed" for name in ("Candidate", "Reopen"))
                                        else "candidate_incomplete")
        require(digest(candidate) == batch["candidate_sha256"] and digest(request_path) == batch["request_sha256"],
                "Candidate or request changed during measurement")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        report["error"] = format_exc()
        raise
    finally:
        try:
            close_document()
        except Exception:
            report["status"] = "failed"
            report["cleanup_error"] = format_exc()
            raise
        finally:
            report["documents_after"] = app.documents.count
            if report["documents_after"] != 0:
                report["status"] = "failed"
            report["ended_utc"] = utc()
            report["elapsed_ns"] = perf_counter_ns() - started
            checkpoint()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare pinned Fusion generation stage scripts without launching Fusion.")
    parser.add_argument("source", type=Path, help="directory with the pinned request, candidate and pending sidecars")
    parser.add_argument("output", type=Path, help="unused stage directory")
    arguments = parser.parse_args()
    print(prepare(arguments.source, arguments.output))
