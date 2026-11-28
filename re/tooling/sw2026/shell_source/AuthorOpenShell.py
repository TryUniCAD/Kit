from __future__ import annotations

import argparse
import hashlib
import json
import math
import secrets
from pathlib import Path

import InspectFresh
import Swapp
from OracleIdentity import application_identity

ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"
SKETCH, STOCK, SHELL = "ShellStockSketch", "ShellStockBoss", "OpenShell"
MARK = 1


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")
        file.flush()


def close_number(actual, expected, label):
    require(math.isclose(actual, expected, rel_tol=4e-7, abs_tol=1e-12), label)


def parameter_name(full_name):
    return "@".join(full_name.split("@")[:2])


def expected(dimensions, edited):
    width, depth, height, original, edit = dimensions
    thickness = edit if edited else original
    inner_width, inner_depth, inner_height = (
        width - 2 * thickness,
        depth - 2 * thickness,
        height - thickness,
    )
    require(
        min(inner_width, inner_depth, inner_height) > 0,
        "shell interior must have positive extents",
    )
    outer_volume = width * depth * height
    inner_volume = inner_width * inner_depth * inner_height
    volume = outer_volume - inner_volume
    area = 2 * (
        width * depth
        + height * (width + depth)
        + inner_height * (inner_width + inner_depth)
    )
    centroid_z = (outer_volume * height - inner_volume * (height + thickness)) / (
        2 * volume
    )
    return volume, area, centroid_z, thickness


def check_geometry(result, dimensions, edited, parameter):
    volume, area, centroid_z, thickness = expected(dimensions, edited)
    require(result["bodies"] == 1, "shell requires one solid")
    mass = result["mass"]
    close_number(mass["volume"], volume, "incorrect shell volume")
    close_number(mass["area"], area, "incorrect shell area")
    for actual, target in zip(mass["com"], (0, 0, centroid_z), strict=True):
        close_number(actual, target, "incorrect shell center of mass")
    features = result["features"]
    require(
        all(
            row["error"] == 0 and row["warning"] is False and row["suppressed"] is False
            for row in features
            if row["name"] in {SKETCH, STOCK, SHELL}
        ),
        "authored shell owners have errors, warnings or suppression",
    )
    owned = [
        (row["name"], row["type"])
        for row in features
        if row["name"] in {SKETCH, STOCK, SHELL}
    ]
    require(
        owned == [(SKETCH, "ProfileFeature"), (STOCK, "Extrusion"), (SHELL, "Shell")],
        "native shell feature order differs",
    )
    shell = next(row for row in features if row["name"] == SHELL)
    owners = [
        row["value"]
        for row in shell.get("dims", ())
        if parameter_name(row["name"]) == parameter
    ]
    require(len(owners) == 1, "shell thickness has no unique display-dimension owner")
    close_number(owners[0], thickness, "incorrect owned shell thickness")


def build_stock(model, dimensions):
    get, invoke = Swapp.cv, Swapp.invoke
    width, depth, height = dimensions[:3]
    require(
        invoke(
            model.Extension,
            "SelectByID2",
            "Front Plane",
            "PLANE",
            0.0,
            0.0,
            0.0,
            False,
            0,
            Swapp.nothing(),
            0,
        ),
        "cannot select the native Front Plane",
    )
    sketch_manager = get(model, "SketchManager")
    invoke(sketch_manager, "InsertSketch", True)
    lines = invoke(
        sketch_manager,
        "CreateCornerRectangle",
        -width / 2,
        -depth / 2,
        0.0,
        width / 2,
        depth / 2,
        0.0,
    )
    require(
        lines is not None and len(lines) == 4,
        "native rectangle did not produce four sketch edges",
    )
    invoke(sketch_manager, "InsertSketch", True)
    sketch_names = [
        row["name"] for row in Swapp.features(model) if row["type"] == "ProfileFeature"
    ]
    require(len(sketch_names) == 1, "native rectangle profile was not uniquely created")
    sketch = invoke(model, "FeatureByName", sketch_names[0])
    sketch.Name = SKETCH
    require(
        invoke(sketch, "Select2", False, 0),
        "cannot select the authored rectangle profile",
    )
    stock = invoke(
        get(model, "FeatureManager"),
        "FeatureExtrusion3",
        True,
        False,
        False,
        0,
        0,
        height,
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        0,
        0.0,
        False,
    )
    require(
        stock is not None and get(stock, "GetTypeName2") == "Extrusion",
        "cannot create the native shell stock",
    )
    stock.Name = STOCK
    require(
        invoke(model, "ForceRebuild3", False) and Swapp.rebuild_errors(model) == 0,
        "native stock rebuild failed",
    )
    require(Swapp.bodies(model) == 1, "stock requires one native solid")
    close_number(
        Swapp.mass(model)["volume"], width * depth * height, "incorrect stock volume"
    )
    return stock


def select_cap(model, stock, dimensions):
    get, invoke = Swapp.cv, Swapp.invoke
    width, depth, height = dimensions[:3]
    candidates = []
    faces = get(stock, "GetFaces")
    require(len(faces) == 6, "stock has no six-face box")
    for face in faces:
        box = tuple(get(face, "GetBox"))
        if len(box) == 6 and all(abs(box[index] - height) <= 1e-7 for index in (2, 5)):
            require(get(get(face, "GetSurface"), "IsPlane"), "cap face must be planar")
            close_number(
                get(face, "GetArea"), width * depth, "incorrect stock cap area"
            )
            candidates.append((face, box))
    require(len(candidates) == 1, "cannot locate one actual cap face")
    face, box = candidates[0]
    extension = model.Extension
    reference = bytes(invoke(extension, "GetPersistReference3", face))
    require(reference, "stock cap has no persistent reference")
    invoke(model, "ClearSelection2", True)
    require(
        invoke(
            extension,
            "SelectByID2",
            "",
            "FACE",
            0.0,
            0.0,
            height,
            False,
            MARK,
            Swapp.nothing(),
            0,
        ),
        "cannot select the actual cap for native shell",
    )
    manager = get(model, "SelectionManager")
    counts = [invoke(manager, "GetSelectedObjectCount2", mark) for mark in (-1, MARK)]
    selected = invoke(manager, "GetSelectedObject6", 1, MARK)
    require(
        counts == [1, 1]
        and selected is not None
        and bytes(invoke(extension, "GetPersistReference3", selected)) == reference,
        "the marked native input must be the actual cap face",
    )
    return {
        "cap_box_m": box,
        "selection_counts": counts,
        "mark": MARK,
        "persistent_reference_sha256": hashlib.sha256(reference).hexdigest(),
    }


def native_state(model, dimensions, edited, parameter):
    require(Swapp.invoke(model, "ForceRebuild3", False), "native shell did not rebuild")
    require(
        Swapp.rebuild_errors(model) == 0, "native shell reported rebuild diagnostics"
    )
    result = {
        "mass": Swapp.mass(model),
        "bodies": Swapp.bodies(model),
        "features": Swapp.features(model),
    }
    require(
        not Swapp.cv(model, "GetBodies2", 1, False),
        "native shell unexpectedly has sheet bodies",
    )
    check_geometry(result, dimensions, edited, parameter)
    return result


def author(controller, case_dir, dimensions, evidence):
    get, invoke = Swapp.cv, Swapp.invoke
    template = Path(controller.template())
    evidence["template_sha256"] = sha256(template)
    model = controller.new_part()
    require(
        sha256(template) == evidence["template_sha256"], "native part template changed"
    )
    stock = build_stock(model, dimensions)
    evidence["selection"] = select_cap(model, stock, dimensions)
    invoke(model, "InsertFeatureShell", dimensions[3], False)
    names = [row["name"] for row in Swapp.features(model) if row["type"] == "Shell"]
    require(len(names) == 1, "native InsertFeatureShell did not create a single Shell")
    feature = invoke(model, "FeatureByName", names[0])
    feature.Name = SHELL
    display = get(feature, "GetFirstDisplayDimension")
    require(
        display is not None, "native shell is missing the thickness display dimension"
    )
    dimension = invoke(display, "GetDimension2", 0)
    require(
        not get(dimension, "ReadOnly") and get(dimension, "DrivenState") == 2,
        "native thickness is not editable",
    )
    evidence["parameter"] = parameter_name(str(get(dimension, "FullName")))
    evidence["original"] = native_state(model, dimensions, False, evidence["parameter"])
    before = case_dir / "OpenShell.SLDPRT"
    evidence["save_original"] = controller.save_as(model, before)
    require(
        evidence["save_original"] == (True, 0, 0), "native original shell save failed"
    )
    evidence["original_sha256"] = sha256(before)
    require(
        invoke(dimension, "SetSystemValue3", dimensions[4], 1, Swapp.nothing()) == 0,
        "native shell thickness edit failed",
    )
    evidence["edited"] = native_state(model, dimensions, True, evidence["parameter"])
    after = case_dir / "OpenShellEdited.SLDPRT"
    evidence["save_edited"] = controller.save_as(model, after)
    require(evidence["save_edited"] == (True, 0, 0), "native edited shell save failed")
    evidence["edited_sha256"] = sha256(after)
    require(
        evidence["edited_sha256"] != evidence["original_sha256"],
        "native edit must change the file",
    )


def check_identity(identity):
    require(
        identity["version_matches"]
        and identity["sha256"] == ORACLE
        and identity["pe_machine"] == "0x8664",
        "unexpected SOLIDWORKS 2026 SP05.2 executable",
    )


def inspect_control(path):
    require(sha256(path) == CONTROL, "independent native control hash differs")
    result = InspectFresh.inspect(path)
    check_identity(result["oracle_identity"])
    require(
        InspectFresh.healthy(result) and sha256(path) == CONTROL,
        "independent native control is unhealthy",
    )
    return result


def capture(case_dir, spec_sha, events):
    spec_path = case_dir / "Request.json"
    require(sha256(spec_path) == spec_sha, "locked source request differs")
    dimensions = tuple(
        json.loads(spec_path.read_text(encoding="utf-8"))["dimensions_m"]
    )
    result = {"request_sha256": spec_sha, "qualified": False}
    with Swapp.Dismisser() as dialog:
        controller = None
        try:
            Swapp.sweep()
            controller = Swapp.Sw()
            result["oracle_identity"] = application_identity(controller.app)
            check_identity(result["oracle_identity"])
            author(controller, case_dir, dimensions, result)
        except Exception as error:
            result["author_exception"] = repr(error)
            raise
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
            result["dialogs"] = dialog.log
            write_json(case_dir / "Author.json", result)
    require(
        not result["controller_diagnostics"] and not dialog.log,
        "native author had application diagnostics",
    )
    events.append(result["oracle_identity"])
    selected = result["parameter"]
    for key, edited in (("original", False), ("edited", True)):
        path = case_dir / ("OpenShellEdited.SLDPRT" if edited else "OpenShell.SLDPRT")
        want = result[key + "_sha256"]
        require(sha256(path) == want, "native source changed before fresh reopen")
        reopened = InspectFresh.inspect(path, parameter_names=(selected,))
        write_json(
            case_dir / ("ReopenEdited.json" if edited else "ReopenOriginal.json"),
            reopened,
        )
        check_identity(reopened["oracle_identity"])
        events.append(reopened["oracle_identity"])
        require(
            InspectFresh.healthy(reopened)
            and reopened["sha256"] == want
            and sha256(path) == want,
            "native shell reopened with errors or changed source bytes",
        )
        check_geometry(reopened, dimensions, edited, selected)
        close_number(
            reopened["parameters"][selected],
            dimensions[4 if edited else 3],
            "reopened shell thickness differs",
        )
    result["qualified"] = True
    require(
        sha256(spec_path) == spec_sha,
        "locked source request changed during native authoring",
    )
    return result


def prepare(root):
    root.mkdir()
    intents = {"disclosed": (0.053, 0.041, 0.028, 0.0028, 0.00353)}
    for name, ranges in (
        (
            "sealed-a",
            ((4360, 5020), (3300, 4050), (2310, 2690), (195, 272), (310, 377)),
        ),
        (
            "sealed-b",
            ((6260, 7580), (4960, 5830), (3110, 3950), (392, 465), (502, 611)),
        ),
    ):
        intents[name] = tuple(
            (first + secrets.randbelow(last - first)) / 100000 for first, last in ranges
        )
    specs = {}
    for name, dimensions in intents.items():
        directory = root / name
        directory.mkdir()
        path = directory / "Request.json"
        write_json(
            path,
            {
                "kind": "front-rectangular-inward-open-top-shell",
                "dimensions_m": dimensions,
            },
        )
        specs[name] = sha256(path)
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    args = parser.parse_args()
    specs = prepare(args.root)
    before = inspect_control(args.control)
    events = [before["oracle_identity"]]
    write_json(args.root / "ControlBefore.json", before)
    cases = {}
    try:
        for name, spec in specs.items():
            Swapp.emit({"stage": "source_start", "case": name, "request_sha256": spec})
            result = capture(args.root / name, spec, events)
            cases[name] = {
                key: result[key]
                for key in (
                    "request_sha256",
                    "qualified",
                    "original_sha256",
                    "edited_sha256",
                )
            }
            Swapp.emit({"stage": "source_locked", "case": name, **cases[name]})
    finally:
        after = inspect_control(args.control)
        write_json(args.root / "ControlAfter.json", after)
        events.append(after["oracle_identity"])
    lifetimes = {item["process_creation_filetime"] for item in events}
    require(
        len(events) == len(lifetimes) == 11,
        "shell source lifecycle requires eleven independent native processes",
    )
    write_json(
        args.root / "Receipt.json",
        {
            "schema": "kit-sw2026-open-shell-source-lock-v1",
            "oracle": {
                "version": "34.5.2.0604",
                "sha256": ORACLE,
                "pe_machine": "0x8664",
                "prog_id": Swapp.PROGID,
            },
            "author_sha256": sha256(Path(__file__)),
            "controls": {
                "before": before["oracle_identity"],
                "after": after["oracle_identity"],
                "sha256": CONTROL,
            },
            "processes": events,
            "cases": cases,
            "shell_writer_code_at_lock": False,
            "new_historical_corpus_credit": 0,
        },
    )
    Swapp.emit(
        {
            "stage": "terminal",
            "receipt_sha256": sha256(args.root / "Receipt.json"),
            "source_count": len(cases),
        }
    )


if __name__ == "__main__":
    main()
