from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isclose, prod
import os
from pathlib import Path
from time import perf_counter_ns
import traceback
from zipfile import ZipFile

import adsk
import adsk.core
import adsk.fusion


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def near(actual, expected):
    return isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)


def point(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def parameter(parameter):
    return {"name": parameter.name, "expression": parameter.expression,
            "database_value": parameter.value, "display_unit": parameter.unit}


def design_for(document):
    require(document is not None, "Fusion did not return a document")
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    require(design is not None, "Fusion document did not contain a design")
    return design


def author(document, dims_mm, anchor_mode, offset_mm=(0.0, 0.0)):
    design = design_for(document)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    root.name = "Saved Cuboid Study"
    for name, value in zip(("kitWidth", "kitDepth", "kitHeight"), dims_mm, strict=True):
        require(design.userParameters.add(name, adsk.core.ValueInput.createByString(f"{value:g} mm"), "mm", "") is not None, f"Could not add {name}")
    x, y = (value / 10.0 for value in offset_mm)
    width, depth, _ = (value / 10.0 for value in dims_mm)
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "Encoder Rectangle"
    lines = sketch.sketchCurves.sketchLines
    low = lines.addByTwoPoints(point(x, y), point(x + width, y))
    right = lines.addByTwoPoints(low.endSketchPoint, point(x + width, y + depth))
    high = lines.addByTwoPoints(right.endSketchPoint, point(x, y + depth))
    left = lines.addByTwoPoints(high.endSketchPoint, low.startSketchPoint)
    constraints = sketch.geometricConstraints
    for line, add in ((low, constraints.addHorizontal), (right, constraints.addVertical),
                      (high, constraints.addHorizontal), (left, constraints.addVertical)):
        require(add(line) is not None, "Could not constrain a rectangle edge")
    corner = low.startSketchPoint
    if anchor_mode == "fixed":
        corner.isFixed = True
    elif anchor_mode == "coincident":
        require(constraints.addCoincident(corner, sketch.originPoint) is not None, "Could not add explicit coincidence")
    dimensions = sketch.sketchDimensions
    axes = adsk.fusion.DimensionOrientations
    for line, axis, label, name in (
        (low, axes.HorizontalDimensionOrientation, point(x + width / 2.0, y - 0.5), "kitWidth"),
        (left, axes.VerticalDimensionOrientation, point(x - 0.5, y + depth / 2.0), "kitDepth"),
    ):
        dimension = dimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint, axis, label)
        require(dimension is not None, f"Could not dimension {name}")
        dimension.parameter.expression = name
    features = root.features.extrudeFeatures
    require(sketch.profiles.count == 1, "Expected one closed rectangle profile")
    feature_input = features.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString("kitHeight"))
    require(feature_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection), "Could not set the positive blind extent")
    extrusion = features.add(feature_input)
    require(extrusion is not None, "Could not create the extrusion")
    extrusion.name = "Encoder Extrusion"
    extrusion.bodies.item(0).name = "Encoder Cuboid"
    require(design.computeAll(), "Authored document did not rebuild")
    return design


def camera_state(app):
    camera = app.activeViewport.camera
    return {"eye_cm": camera.eye.asArray(), "target_cm": camera.target.asArray(), "up": camera.upVector.asArray()}


def observe(app, design):
    root = design.rootComponent
    require(root.sketches.count == 1 and root.bRepBodies.count == 1, "Expected a single sketch and body")
    sketch = root.sketches.item(0)
    points = list(sketch.sketchPoints)
    lines = list(sketch.sketchCurves.sketchLines)

    def point_index(entity):
        return next((index for index, value in enumerate(points) if value == entity), None)

    def line_index(entity):
        return next((index for index, value in enumerate(lines) if value == entity), None)

    points_data = []
    for index, entity in enumerate(points):
        token = entity.entityToken
        resolved = design.findEntityByToken(token)
        points_data.append({
            "index": index,
            "is_origin": entity == sketch.originPoint,
            "fixed": entity.isFixed,
            "fully_constrained": entity.isFullyConstrained,
            "xyz_cm": entity.geometry.asArray(),
            "same_entity_token_lookup": any(item == entity for item in resolved),
        })
    constraint_data = []
    for entity in sketch.geometricConstraints:
        row = {"type": entity.objectType}
        if entity.objectType == adsk.fusion.CoincidentConstraint.classType():
            row.update(point=point_index(entity.point), other_point=point_index(entity.entity),
                       other_line=line_index(entity.entity))
        elif hasattr(entity, "line"):
            row["line"] = line_index(entity.line)
        constraint_data.append(row)
    feature = root.features.extrudeFeatures.item(0)
    extent = adsk.fusion.DistanceExtentDefinition.cast(feature.extentOne)
    require(extent is not None, "Expected a distance extrusion")
    body = root.bRepBodies.item(0)
    physical = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    return {
        "configured_design": design.isConfiguredDesign,
        "camera": camera_state(app),
        "parameters": [parameter(item) for item in design.allParameters],
        "sketch": {
            "name": sketch.name,
            "support_plane": root.xYConstructionPlane.name,
            "fully_constrained": sketch.isFullyConstrained,
            "profile_count": sketch.profiles.count,
            "origin_point": point_index(sketch.originPoint),
            "points": points_data,
            "lines": [[point_index(line.startSketchPoint), point_index(line.endSketchPoint)] for line in lines],
            "fixed_corner_positions_cm": [row["xyz_cm"] for row in points_data if row["fixed"] and not row["is_origin"]],
            "constraints": constraint_data,
            "dimensions": [{"type": dim.objectType, "driving": dim.isDriving, **parameter(dim.parameter)}
                           for dim in sketch.sketchDimensions],
        },
        "timeline": [{"name": item.name, "health": int(item.healthState), "suppressed": item.isSuppressed,
                      "message": item.errorOrWarningMessage} for item in design.timeline],
        "extrusion": {"name": feature.name, "operation": int(feature.operation), "distance": parameter(extent.distance)},
        "body": {"name": body.name, "volume_cm3": body.volume, "area_cm2": physical.area,
                 "center_cm": physical.centerOfMass.asArray(),
                 "min_cm": body.boundingBox.minPoint.asArray(), "max_cm": body.boundingBox.maxPoint.asArray(),
                 "topology": [body.faces.count, body.edges.count, body.vertices.count],
                 "light_bulb": body.isLightBulbOn, "visible": body.isVisible},
    }


def check(state, dims_mm, mode, offset_mm=(0.0, 0.0)):
    width, depth, height = (value / 10.0 for value in dims_mm)
    left, low = (value / 10.0 for value in offset_mm)
    sketch, body = state["sketch"], state["body"]
    require(not state["configured_design"], "Expected the local unconfigured design")
    require(len(sketch["points"]) == 5 and len(sketch["lines"]) == 4 and sketch["profile_count"] == 1, "Expected the full closed rectangle inventory")
    require(sketch["origin_point"] is not None and all(row["same_entity_token_lookup"] for row in sketch["points"]), "Could not establish sketch point identities")
    names = {dim["expression"] for dim in sketch["dimensions"] if dim["driving"]}
    require(names == {"kitWidth", "kitDepth"} and len(sketch["dimensions"]) == 2, "Width/depth dimensions differ")
    require(state["extrusion"]["distance"]["expression"] == "kitHeight", "Extrusion is not linked to the height driver")
    require(len(sketch["constraints"]) == (5 if mode == "coincident" else 4), "Anchor/axis constraint count differs")
    require(sketch["fully_constrained"] == (mode != "free"), "Unexpected native sketch solver state")
    fixed = sketch["fixed_corner_positions_cm"]
    if mode == "fixed":
        require(len(fixed) == 1 and all(near(a, b) for a, b in zip(fixed[0], (left, low, 0))), "Fixed corner position differs")
    else:
        require(not fixed, "Unexpected fixed corner")
    require(len(state["timeline"]) == 2 and all(row["health"] == 0 and not row["suppressed"] and not row["message"] for row in state["timeline"]), "Timeline is unhealthy")
    require(body["topology"] == [6, 12, 8] and near(body["volume_cm3"], prod((width, depth, height))), "Unexpected cuboid topology or volume")
    require(near(body["area_cm2"], 2 * (width * depth + width * height + depth * height)), "Unexpected cuboid area")
    if mode != "free":
        for field, expected in (("min_cm", (left, low, 0)), ("max_cm", (left + width, low + depth, height)),
                                ("center_cm", (left + width / 2, low + depth / 2, height / 2))):
            require(all(near(a, b) for a, b in zip(body[field], expected)), f"Unexpected cuboid {field}")


def export(design, path):
    require(not path.exists(), "Capture destination already exists")
    options = design.exportManager.createFusionArchiveExportOptions(str(path))
    require(design.exportManager.execute(options), "Fusion local archive export failed")
    with ZipFile(path) as archive:
        members = [{"name": item.filename, "size": item.file_size, "crc32": f"{item.CRC:08x}",
                    "method": item.compress_type} for item in archive.infolist() if not item.is_dir()]
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path), "members": members}


def capture(config_path):
    app = adsk.core.Application.get()
    settings = json.loads(config_path.read_bytes())
    output = config_path.parent
    receipt = output / "Capture.json"
    require(not receipt.exists(), "Capture receipt already exists")
    report = {"schema": "kit.fusion.saved-cuboid-capture/1", "group": settings["group"],
              "request_sha256": digest(config_path), "script_sha256": settings["capture_script_sha256"],
              "fusion_version": app.version, "pid": os.getpid(), "started_utc": utc_now(),
              "documents_before": app.documents.count, "status": "running", "cases": []}
    started = perf_counter_ns()
    document = None

    def checkpoint():
        tmp = receipt.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        tmp.replace(receipt)

    def close_document():
        nonlocal document
        if document is not None:
            require(document.close(False), "Could not close the capture document")
            document = None

    def build(dims, mode, offset=(0.0, 0.0)):
        nonlocal document
        require(document is None and app.documents.count == 0, "Prior document still open")
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        return author(document, dims, mode, offset)

    def snapshot(name, design, dims, mode, offset=(0.0, 0.0), varied=None):
        report["last_operation"] = f"observe {name}"
        checkpoint()
        state = observe(app, design)
        check(state, dims, mode, offset)
        row = {"name": name, "captured_utc": utc_now(), "dimensions_mm": dims,
               "offset_mm": offset, "anchor_mode": mode, "varied": varied, "measurement": state}
        report["last_operation"] = f"local export {name}"
        checkpoint()
        row["archive"] = export(design, output / f"{name}.f3d")
        report["cases"].append(row)
        checkpoint()
        return row["archive"]

    def healthy_control(name, archive):
        nonlocal document
        path = output / archive["name"]
        report["last_operation"] = f"open independent {name} control"
        checkpoint()
        require(digest(path) == archive["sha256"], "Independent control archive changed")
        options = app.importManager.createFusionArchiveImportOptions(str(path))
        document = app.importManager.importToNewDocument(options)
        design = design_for(document)
        require(design.computeAll(), "Independent control did not rebuild")
        state = observe(app, design)
        check(state, control_dims, "fixed")
        report[name] = {"sha256": archive["sha256"], "measurement": state}
        close_document()
        checkpoint()

    def change_height(design, height):
        design.userParameters.itemByName("kitHeight").expression = f"{height:g} mm"
        require(design.computeAll(), "Height edit did not rebuild")

    control_dims = (37.0, 16.0, 8.0)
    try:
        require(report["documents_before"] == 0, "The task-owned Fusion process must start without open documents")
        control = build(control_dims, "fixed")
        control_archive = snapshot("IndependentControl", control, control_dims, "fixed")
        close_document()
        healthy_control("control_before", control_archive)
        reference = (18.7, 24.9, 11.3)
        if settings["group"] == "anchor":
            for name, mode, offset in (("FixedOrigin", "fixed", (0.0, 0.0)),
                                       ("CoincidentOrigin", "coincident", (0.0, 0.0)),
                                       ("CoincidentCoordinatesOnly", "free", (0.0, 0.0)),
                                       ("FixedOffset", "fixed", (-14.2, 7.9))):
                design = build(reference, mode, offset)
                snapshot(name, design, reference, mode, offset, "anchor")
                close_document()
        elif settings["group"] == "auxiliary":
            design = build(reference, "fixed")
            snapshot("Original", design, reference, "fixed")
            snapshot("Repeated", design, reference, "fixed", varied="no authored change")
            viewport = app.activeViewport
            original_camera = viewport.camera
            front = viewport.camera
            front.viewOrientation = adsk.core.ViewOrientations.FrontViewOrientation
            front.isSmoothTransition = False
            viewport.camera = front
            adsk.doEvents()
            require(camera_state(app) != report["cases"][-1]["measurement"]["camera"], "Camera did not change")
            snapshot("CameraOnly", design, reference, "fixed", varied="viewport camera")
            original_camera.isSmoothTransition = False
            viewport.camera = original_camera
            body = design.rootComponent.bRepBodies.item(0)
            body.isLightBulbOn = False
            adsk.doEvents()
            require(not body.isVisible, "Body display visibility did not change")
            snapshot("HiddenOnly", design, reference, "fixed", varied="body display visibility")
            body.isLightBulbOn = True
            changed = (*reference[:2], 32.6)
            change_height(design, changed[2])
            snapshot("HeightOnly", design, changed, "fixed", varied="height driver")
            close_document()
        elif settings["group"] == "holdout":
            for item in settings["holdout"]:
                dims = item["dimensions_mm"]
                design = build(dims, "fixed")
                snapshot(item["name"] + "Initial", design, dims, "fixed")
                edited = (*dims[:2], item["edited_height_mm"])
                change_height(design, edited[2])
                snapshot(item["name"] + "Edited", design, edited, "fixed", varied="height driver")
                close_document()
        else:
            raise ValueError("Unknown corpus capture group")
        healthy_control("control_after", control_archive)
        require(app.documents.count == 0, "An unrelated or capture document remains open")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
        raise
    finally:
        try:
            close_document()
        finally:
            report["documents_after"] = app.documents.count
            report["ended_utc"] = utc_now()
            report["elapsed_ns"] = perf_counter_ns() - started
            checkpoint()
