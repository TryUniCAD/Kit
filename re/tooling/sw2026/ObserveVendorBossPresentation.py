from argparse import ArgumentParser
from functools import partial
import json
from pathlib import Path
import subprocess
import sys

from ObserveVendorBossCorpus import (
    demand,
    digest,
    inspect_saved,
    observe_part,
    phase,
    read_json,
    write_json,
)


OPEN_READ_ONLY_SILENT = 3


def array(value):
    return () if value is None else tuple(value)


def annotation_row(view, member):
    rotation = member(view, "GetViewRotation")
    if rotation is not None and not isinstance(rotation, (list, tuple)):
        rotation = member(rotation, "ArrayData")
    return {
        "shown": bool(member(view, "IsShown")),
        "annotation_count": int(member(view, "AnnotationCount")),
        "always_2d": bool(member(view, "Always2D")),
        "unassigned": bool(member(view, "UnassignedView")),
        "flat_pattern": bool(member(view, "FlatPatternView")),
        "rotation": array(rotation),
    }


def observe_annotations(extension, member):
    views = array(member(extension, "AnnotationViews"))
    count = int(member(extension, "AnnotationViewCount"))
    demand(len(views) == count, "native annotation view roster disagrees with its count")
    active = member(extension, "GetActiveAnnotationView")
    return {
        "view_count": count,
        "total_annotations": int(member(extension, "GetAnnotationCount")),
        "views": [annotation_row(view, member) for view in views],
        "active_view": annotation_row(active, member) if active is not None else None,
    }


def read_light_property(document, index):
    import pythoncom

    dispatch = document._oleobj_
    identifier = dispatch.GetIDsOfNames("LightSourcePropertyValues")
    return dispatch.InvokeTypes(
        identifier, 0, pythoncom.DISPATCH_PROPERTYGET, (pythoncom.VT_VARIANT, 0),
        ((pythoncom.VT_I4, 1),), index,
    )


def observe_lights(document, member):
    count = int(member(document, "GetLightSourceCount"))
    demand(0 <= count <= 64, "native light roster exceeds its bounded domain")
    return [
        {"index": index, "name": document.GetLightSourceName(index),
         "property_values": array(read_light_property(document, index))}
        for index in range(count)
    ]


def observe_display(document, extension, config, member):
    states = array(member(config, "GetDisplayStates"))
    count = int(member(config, "GetDisplayStatesCount"))
    demand(len(states) == count, "native display state roster disagrees with its count")
    names = ("Front Plane", "Top Plane", "Right Plane", "Origin", "Sketch1")
    return {
        "configuration": str(member(config, "Name")),
        "display_states": states,
        "linked_display_state": bool(member(extension, "LinkedDisplayState")),
        "construct_planes_visible": bool(member(document, "GetVisibilityOfConstructPlanes")),
        "visible_solids": len(document.GetBodies2(0, True) or ()),
        "feature_visibility": {
            name: int(member(document.FeatureByName(name), "Visible")) for name in names
        },
    }


def observe_material(document, extension, config, member):
    import pythoncom
    from win32com.client import VARIANT

    database = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "")
    material_name = document.GetMaterialPropertyName2(str(member(config, "Name")), database)
    members = array(member(extension, "GetRenderMaterials"))
    count = int(member(extension, "GetRenderMaterialsCount"))
    demand(len(members) == count, "native appearance roster disagrees with its count")
    return {
        "assigned_name": material_name,
        "material_database": database.value,
        "model_property_values": array(member(document, "MaterialPropertyValues")),
        "render_appearances": [
            {"filename": str(member(material, "FileName")),
             "primary_color": int(member(material, "PrimaryColor")),
             "secondary_color": int(member(material, "SecondaryColor")),
             "tertiary_color": int(member(material, "TertiaryColor")),
             "linked_display_states": array(member(material, "GetLinkedDisplayStates"))}
            for material in members
        ],
    }


def observe_presentation(base, document):
    member = base.member
    demand(member(document, "IsOpenedReadOnly"), "native document did not open read-only")
    extension = document.Extension
    config = document.ConfigurationManager.ActiveConfiguration
    return {
        **observe_part(base, document),
        "read_only": True,
        "annotation_views": observe_annotations(extension, member),
        "lights": observe_lights(document, member),
        "display": observe_display(document, extension, config, member),
        "material": observe_material(document, extension, config, member),
    }


def measure(args):
    source = read_json(args.plan)
    phase_labels = ("ControlBefore", "VendorReference", "SavedKitEdit", "ControlAfter")
    results = {}
    root = args.root.resolve(strict=True)
    binary = args.executable.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir()

    def run(label, request):
        source_path = Path(request["path"]).resolve(strict=True)
        demand(digest(source_path) == request["sha256"], "native input differs from its retained source digest")
        folder = output / label
        folder.mkdir()
        request_file = folder / "Request.json"
        report_file = folder / "Record.json"
        write_json(request_file, {
            **request, "role": label, "operation": "measure", "executable": str(binary),
            "executable_sha256": args.executable_sha256, "property": None,
        })
        command = (
            sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(root),
            "phase", str(request_file), str(report_file),
        )
        with (folder / "Worker.log").open("xb") as log:
            try:
                work = subprocess.run(
                    command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False,
                )
            except subprocess.TimeoutExpired:
                return {"passed": False, "error": "owned worker exceeded 180 seconds"}
        if not report_file.is_file():
            return {"passed": False, "worker_exit_code": work.returncode,
                    "error": "owned worker issued no result"}
        return {
            **read_json(report_file), "worker_exit_code": work.returncode,
            "record_sha256": digest(report_file), "request_sha256": digest(request_file),
            "source_unchanged": digest(source_path) == request["sha256"],
        }

    results["ControlBefore"] = run("ControlBefore", source["Control"])
    if results["ControlBefore"]["passed"]:
        for label in phase_labels[1:3]:
            results[label] = run(label, source[label])
    results["ControlAfter"] = run("ControlAfter", source["Control"])
    births = {
        (row["oracle_identity"]["pid"], row["oracle_identity"]["started"])
        for row in results.values() if "oracle_identity" in row
    }
    valid = len(births) == len(results) == 4 and all(
        row["passed"] and row["worker_exit_code"] == 0 and row["source_unchanged"]
        for row in results.values()
    )
    report_file = output / "Result.json"
    write_json(report_file, {
        "schema": "kit.sw2026.vendor-boss-presentation-contrast.v1", "passed": valid,
        "controls_healthy": results["ControlBefore"]["passed"] and results["ControlAfter"]["passed"],
        "executable_sha256": args.executable_sha256, "distinct_native_processes": len(births),
        "plan_sha256": digest(args.plan), "method_sha256": digest(Path(__file__)),
        "owner_harness_sha256": digest(Path(__file__).with_name("ObserveVendorBossCorpus.py")),
        "phases": results,
    })
    print(json.dumps({"passed": valid, "result_sha256": digest(report_file), "phases": len(results)}))
    return 0 if valid else 1


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    modes = parser.add_subparsers(dest="mode", required=True)
    batch = modes.add_parser("measure")
    batch.add_argument("--plan", type=Path, required=True)
    batch.add_argument("--output", type=Path, required=True)
    batch.add_argument("--executable", type=Path, required=True)
    batch.add_argument("--executable-sha256", required=True)
    child = modes.add_parser("phase")
    child.add_argument("request", type=Path)
    child.add_argument("output", type=Path)
    options = parser.parse_args()
    if options.mode == "phase":
        inspect = partial(inspect_saved, observe=observe_presentation, open_options=OPEN_READ_ONLY_SILENT)
        raise SystemExit(phase(options.root, read_json(options.request), options.output, inspect=inspect))
    raise SystemExit(measure(options))
