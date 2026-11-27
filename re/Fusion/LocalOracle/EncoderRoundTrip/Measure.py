from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


SKETCH_NAME = "Encoder Rectangle"
EXTRUSION_NAME = "Encoder Extrusion"
BODY_NAME = "Encoder Cuboid"
STAGES = ("ControlBefore", "Candidate", "Reopen", "ControlAfter")
TOLERANCE = 1e-8


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def close(actual, expected):
    return isclose(actual, expected, rel_tol=TOLERANCE, abs_tol=TOLERANCE)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def expression(mm):
    return f"{mm:g} mm"


def design_for(document):
    require(document is not None, "Fusion did not open a design document")
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    require(design is not None, "Document lacks a Fusion design")
    return design


def export(design, filename):
    require(not filename.exists(), f"Export already exists: {filename.name}")
    options = design.exportManager.createFusionArchiveExportOptions(str(filename))
    require(design.exportManager.execute(options), f"Fusion export failed: {filename.name}")
    return digest(filename)


def native_control(document, width_mm, depth_mm, height_mm):
    design = design_for(document)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    component = design.rootComponent
    for name, mm in (("kitWidth", width_mm), ("kitDepth", depth_mm), ("kitHeight", height_mm)):
        value = adsk.core.ValueInput.createByString(expression(mm))
        require(design.userParameters.add(name, value, "mm", ""), f"Cannot create {name}")
    point = adsk.core.Point3D.create
    width_cm, depth_cm = width_mm / 10, depth_mm / 10
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = SKETCH_NAME
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        point(0, 0, 0), point(width_cm, depth_cm, 0),
    )
    bottom = next(line for line in lines if all(close(vertex.geometry.y, 0) for vertex in (line.startSketchPoint, line.endSketchPoint)))
    left = next(line for line in lines if all(close(vertex.geometry.x, 0) for vertex in (line.startSketchPoint, line.endSketchPoint)))
    for line in lines:
        start, end = line.startSketchPoint.geometry, line.endSketchPoint.geometry
        if close(start.y, end.y):
            sketch.geometricConstraints.addHorizontal(line)
        else:
            sketch.geometricConstraints.addVertical(line)
    anchor = next(vertex for vertex in (bottom.startSketchPoint, bottom.endSketchPoint) if close(vertex.geometry.x, 0))
    anchor.isFixed = True
    for line, orientation, location, parameter in (
        (bottom, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, point(width_cm / 2, -0.5, 0), "kitWidth"),
        (left, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, point(-0.5, depth_cm / 2, 0), "kitDepth"),
    ):
        dimension = sketch.sketchDimensions.addDistanceDimension(
            line.startSketchPoint, line.endSketchPoint, orientation, location,
        )
        require(dimension is not None, f"Could not add {parameter} dimension")
        dimension.parameter.expression = parameter
    extrusions = component.features.extrudeFeatures
    feature_input = extrusions.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    height = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString("kitHeight"))
    require(feature_input.setOneSideExtent(height, adsk.fusion.ExtentDirections.PositiveExtentDirection), "Could not set control extent")
    extrusion = extrusions.add(feature_input)
    require(extrusion is not None, "Could not create independent control extrusion")
    extrusion.name = EXTRUSION_NAME
    extrusion.bodies.item(0).name = BODY_NAME
    return design


def observe(design):
    root = design.rootComponent
    sketches = [{
        "name": sketch.name,
        "type": sketch.objectType,
        "fully_constrained": sketch.isFullyConstrained,
        "constraints": sorted(value.objectType for value in sketch.geometricConstraints),
        "dimensions": sorted(value.parameter.expression for value in sketch.sketchDimensions),
        "profiles": sketch.profiles.count,
        "lines_cm": [[line.startSketchPoint.geometry.asArray(), line.endSketchPoint.geometry.asArray()]
                     for line in sketch.sketchCurves.sketchLines],
    } for sketch in root.sketches]
    bodies = []
    for body in root.bRepBodies:
        props = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        bodies.append({
            "name": body.name,
            "solid": body.isSolid,
            "volume_cm3": body.volume,
            "area_cm2": props.area,
            "center_cm": props.centerOfMass.asArray(),
            "min_cm": body.boundingBox.minPoint.asArray(),
            "max_cm": body.boundingBox.maxPoint.asArray(),
            "topology": (body.faces.count, body.edges.count, body.vertices.count),
            "material": body.material.name if body.material is not None else None,
            "mass_kg": props.mass,
            "density_kg_per_cm3": props.density,
        })
    timeline = []
    for node in design.timeline:
        entity = node.entity
        timeline.append({
            "name": node.name,
            "type": entity.objectType if entity is not None else None,
            "suppressed": node.isSuppressed,
            "health": int(node.healthState),
            "message": node.errorOrWarningMessage,
        })
    return {
        "parametric": design.designType == adsk.fusion.DesignTypes.ParametricDesignType,
        "sketches": sketches,
        "bodies": bodies,
        "timeline": timeline,
        "user_parameters": {parameter.name: {"expression": parameter.expression, "internal_value": parameter.value,
                                             "display_unit": parameter.unit} for parameter in design.userParameters},
        "model_parameters": [{"name": parameter.name, "expression": parameter.expression, "internal_value": parameter.value,
                              "display_unit": parameter.unit} for parameter in design.allParameters],
        "origin_planes": [root.xYConstructionPlane.name, root.xZConstructionPlane.name, root.yZConstructionPlane.name],
        "origin": root.originConstructionPoint.geometry.asArray(),
    }


def require_shape(state, width_mm, depth_mm, height_mm, candidate):
    width, depth, height = width_mm / 10, depth_mm / 10, height_mm / 10
    require(state["parametric"], "Design history is disabled")
    require(len(state["sketches"]) == len(state["bodies"]) == 1, "Expected one sketch and one body")
    timeline = state["timeline"]
    require([(node["name"], node["type"]) for node in timeline] == [
        (SKETCH_NAME, adsk.fusion.Sketch.classType()),
        (EXTRUSION_NAME, adsk.fusion.ExtrudeFeature.classType()),
    ], "Timeline names or types differ")
    require(all(node["health"] == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState and not node["message"]
                and not node["suppressed"] for node in timeline), "Timeline contains an unhealthy or suppressed feature")
    sketch = state["sketches"][0]
    require(sketch["fully_constrained"] and sketch["profiles"] == 1 and len(sketch["lines_cm"]) == 4, "Expected a fully constrained, closed four-line sketch")
    require(sketch["dimensions"] == ["kitDepth", "kitWidth"], "Rectangle dimension bindings differ")
    require(len(sketch["constraints"]) >= 4, "Rectangle orientation constraints are missing")
    if candidate:
        require(len(sketch["constraints"]) == 4, "Candidate rectangle constraint count differs")
        require({item["expression"] for item in state["model_parameters"]}.issuperset({"kitHeight", "kitWidth", "kitDepth"}), "Candidate model parameter bindings differ")
    require(all(close(value, 0) for value in state["origin"]), "Root origin differs")
    corners = ((0, 0, 0), (width, 0, 0), (width, depth, 0), (0, depth, 0))
    actual = [point for line in sketch["lines_cm"] for point in line]
    matches = [sum(all(close(a, b) for a, b in zip(point, corner, strict=True)) for point in actual) for corner in corners]
    require(matches == [2] * 4, "Rectangle corners differ")
    for name, expected in (("kitWidth", width), ("kitDepth", depth), ("kitHeight", height)):
        require(close(state["user_parameters"][name]["internal_value"], expected), f"{name} value differs")
    body = state["bodies"][0]
    require(body["solid"] and body["name"] == BODY_NAME and body["topology"] == (6, 12, 8), "Body identity or topology differs")
    expected_area = 2 * (width * depth + width * height + depth * height)
    for label, wanted in (("volume_cm3", width * depth * height), ("area_cm2", expected_area)):
        require(close(body[label], wanted), f"Body {label} differs")
    for label, wanted in (("min_cm", (0, 0, 0)), ("max_cm", (width, depth, height)),
                          ("center_cm", (width / 2, depth / 2, height / 2))):
        require(all(close(a, b) for a, b in zip(body[label], wanted, strict=True)), f"Body {label} differs")
    require(body["material"] is not None and body["density_kg_per_cm3"] > 0, "Invalid native body material")
    require(close(body["mass_kg"], body["volume_cm3"] * body["density_kg_per_cm3"]), "Body mass and density disagree")


def measure(config_path, stage):
    app = adsk.core.Application.get()
    root = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    receipt = root / f"{stage}.json"
    require(not receipt.exists(), f"Stage receipt already exists: {stage}")
    control_file = root / "VendorControl.f3d"
    edited_file = root / "VendorEdited.f3d"
    restored_file = root / "VendorRestored.f3d"
    report = {
        "stage": stage,
        "case": config["case"],
        "role": config["role"],
        "source_sha256": config["source_sha256"],
        "candidate_sha256": config["candidate_sha256"],
        "batch_sha256": digest(config_path),
        "measurement_script_sha256": config["measurement_script_sha256"],
        "fusion_version": app.version,
        "pid": os.getpid(),
        "documents_before": app.documents.count,
        "status": "running",
        "measurements": {},
        "archives": {},
    }
    document = None

    def checkpoint():
        temporary = receipt.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temporary.replace(receipt)

    def at(operation):
        report["last_operation"] = operation
        checkpoint()

    def check(label, design, height, rebuild=False):
        at(label)
        if rebuild:
            require(design.computeAll(), "Fusion computeAll returned failure")
        state = observe(design)
        report["measurements"][label] = state
        checkpoint()
        require_shape(state, width_mm, depth_mm, height, stage in ("Candidate", "Reopen"))

    def open_archive(filename, expected_digest):
        nonlocal document
        require(document is None, "A prior oracle document is still open")
        file_digest = digest(filename)
        report["archives"][filename.name] = file_digest
        require(file_digest == expected_digest, f"Archive hash differs: {filename.name}")
        at(f"import {filename.name}")
        options = app.importManager.createFusionArchiveImportOptions(str(filename))
        document = app.importManager.importToNewDocument(options)
        return design_for(document)

    def close_document():
        nonlocal document
        if document is not None:
            require(document.close(False), "Could not close the oracle document")
            document = None

    def save(design, filename):
        at(f"export {filename.name}")
        report["archives"][filename.name] = export(design, filename)
        checkpoint()

    def previous_reports():
        earlier = STAGES[:STAGES.index(stage)]
        reports = {}
        for name in earlier:
            path = root / f"{name}.json"
            if name == "Reopen" and not path.exists() and reports["Candidate"]["status"] != "passed":
                continue
            result = json.loads(path.read_text(encoding="utf-8"))
            require(result["batch_sha256"] == report["batch_sha256"], f"{name} belongs to another batch")
            require(result["fusion_version"] == report["fusion_version"], f"Fusion version changed after {name}")
            require(result["pid"] != report["pid"], f"{stage} must start in a fresh Fusion process after {name}")
            reports[name] = result
        return reports

    width_mm, depth_mm = config["width_mm"], config["depth_mm"]
    encoded_height, native_edit = config["encoded_height_mm"], config["native_edit_mm"]
    checkpoint()
    try:
        require(report["documents_before"] == 0, "Oracle requires a fresh process with zero unrelated open documents")
        earlier = previous_reports()
        if stage == "ControlBefore":
            at("author control through Fusion API")
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = native_control(document, width_mm, depth_mm, encoded_height)
            check("authored", design, encoded_height, rebuild=True)
            save(design, control_file)
            close_document()
            design = open_archive(control_file, report["archives"][control_file.name])
            check("opened", design, encoded_height)
            check("rebuilt", design, encoded_height, rebuild=True)
        elif stage == "Candidate":
            require(earlier["ControlBefore"]["status"] == "passed", "Starting control is unhealthy")
            design = open_archive(Path(config["candidate"]), config["candidate_sha256"])
            check("opened", design, encoded_height)
            check("rebuilt", design, encoded_height, rebuild=True)
            at("roll back extrusion")
            design.timeline.markerPosition = 1
            report["rollback_body_count"] = design.rootComponent.bRepBodies.count
            require(report["rollback_body_count"] == 0, "Timeline rollback retained a solid")
            require(design.timeline.moveToEnd(), "Timeline restoration failed")
            check("rolled_forward", design, encoded_height, rebuild=True)
            height = design.userParameters.itemByName("kitHeight")
            original_expression = height.expression
            at("edit kitHeight")
            height.expression = expression(native_edit)
            check("edited", design, native_edit, rebuild=True)
            save(design, edited_file)
            at("restore kitHeight")
            height.expression = original_expression
            check("restored", design, encoded_height, rebuild=True)
            save(design, restored_file)
        elif stage == "Reopen":
            require(earlier["Candidate"]["status"] == "passed", "Candidate did not save both states")
            for label, filename, height in (("edited_reopened", edited_file, native_edit),
                                            ("restored_reopened", restored_file, encoded_height)):
                design = open_archive(filename, earlier["Candidate"]["archives"][filename.name])
                check(label, design, height, rebuild=True)
                close_document()
        else:
            require(earlier["ControlBefore"]["status"] == "passed", "Starting control is unhealthy")
            design = open_archive(control_file, earlier["ControlBefore"]["archives"][control_file.name])
            check("opened", design, encoded_height)
            check("rebuilt", design, encoded_height, rebuild=True)
            design.userParameters.itemByName("kitHeight").expression = expression(native_edit)
            check("edited", design, native_edit, rebuild=True)
            report["batch_status"] = ("native_measurements_passed" if
                                      all(earlier[name]["status"] == "passed" for name in ("Candidate", "Reopen"))
                                      else "candidate_unqualified")
        close_document()
        if stage == "Candidate":
            require(digest(Path(config["candidate"])) == config["candidate_sha256"], "Fusion mutated the candidate file")
        require(app.documents.count == 0, "Oracle left a document open")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
        raise
    finally:
        try:
            close_document()
        except Exception:
            report["status"] = "failed"
            report["cleanup_error"] = traceback.format_exc()
        report["documents_after"] = app.documents.count
        checkpoint()
