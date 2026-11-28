from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import hypot, isclose
from pathlib import Path, PureWindowsPath
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
TOOLS = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(REPO), str(TOOLS), str(TOOLS / "serial"), str(HERE)]

from AuthorSdkCircleRequests import make_document
from ProjectConcentricRadialIntent import light_values, read_intents
from ProjectD01Concentric import project_d01, require
from ProveConcentricSourceBrep import D01_LOCKED, checked, json_digest, source_case
from ProveD01ConcentricBridge import AUTHOR, FILES, LOCK, proof_guard

from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import RadialLabelIn
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylAsm import PrepCylAsm
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadRadialDrive import ReadRadialDrive
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


BASE = "0cd00727bac5068f3a21df07d6e3981b6cef3f69"


def fingerprint(data):
    return sha256(data).hexdigest()


def point(value):
    return tuple(value[key] for key in "xyz")


def owned_label(link):
    features = IndexFeatures(link)
    boss, = [node for node in features.values() if node.ClassValue.NameValue == "moExtrusion_c"]
    ended = ReadExtrude(link, boss, features)
    sketch = ended.ProfileValue.FieldsValue["pd_f80"]
    driver, mode, dimension = ReadRadialDrive(link, sketch)
    view_index = driver.TypedOwner["display_index"]
    display, = [entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue
                if entry.IndexValue == view_index]
    values = display.FieldsValue
    handle, = values["f850"]
    display_owner, = sketch.FieldsValue["dims"]["f118"].FieldsValue["items"]
    require(display.ClassValue.NameValue == "moDisplayRadialDim_c"
            and display_owner["o"] is display
            and handle["o"].FieldsValue["ff0"] is sketch
            and handle["o"].IndexValue == driver.TypedOwner["handle_index"]
            and dimension.FieldsValue["f28"].IndexValue == driver.TypedOwner["object_index"],
            "radial text must belong to the actual linked sketch driver")
    return {
        "text": point(values["f6a0"]["f38"]),
        "direction": point(values["f880"]),
        "centre": point(values["f958"]),
        "second_centre": point(values["f988"]),
        "radial_scale": values["f8a8"],
        "radial_offset": values["f8b0"],
        "radius_or_diameter_m": values["f950"],
        "mode": mode,
        "driver_name": driver.name,
        "depth_mm": ended.RequireDepth().DepthValue.value_mm,
        "dimension_id": dimension.FieldsValue["f50"],
        "display_index": view_index,
        "parameter_index": driver.TypedOwner["object_index"],
    }


def changed_streams(first, second):
    left = SldprtArchive.from_bytes(first).streams
    right = SldprtArchive.from_bytes(second).streams
    require(set(left) == set(right), "radial text changed the part stream inventory")
    return sorted(key for key in left if left[key] != right[key])


def refusal_checks(build, label, depth_id):
    cases = (
        ("foreign_sketch", lambda: build(replace(label, SketchId="sketch/foreign")),
         "actual owned sketch and radial driver"),
        ("same_named_depth_driver", lambda: build(replace(label, ParameterId=depth_id)),
         "actual owned sketch and radial driver"),
        ("boolean_coordinate", lambda: build(replace(label, TextPoint=(*label.TextPoint[:2], True))),
         "coordinate or scale must be a real numeric value"),
        ("nonfinite_coordinate", lambda: build(replace(label, TextPoint=(*label.TextPoint[:2], float("inf")))),
         "coordinate or scale must be finite"),
        ("short_point", lambda: build(replace(label, TextPoint=label.TextPoint[:2])),
         "three sketch frame coordinates"),
    )
    result = {}
    for name, call, expected in cases:
        try:
            call()
        except (ValueError, TypeError) as error:
            require(expected in str(error), "unexpected label refusal: " + str(error))
            result[name] = str(error)
        else:
            raise ValueError("unqualified label was generated: " + name)
    return result


def run_worker(request):
    document = FromData(request["document"])
    phase = request["phase"]
    epoch = request["written_at"]
    destination = request["destination"]
    fields = request["label"]
    label = RadialLabelIn(fields["SketchId"], fields["ParameterId"], tuple(fields["TextPoint"]))
    planar = replace(label, TextPoint=(*label.TextPoint[:2], 0.0))
    if phase == "RightContrast":
        part = document
        output = SelfFileInput(destination, epoch)
        recipe = MakePartRecipe(PlanCircle(part), epoch)
        inputs = BindPartIntent(part, PlanCircle(part), recipe, output)

        def build(value):
            return MakeCirclePart(part, inputs, LabelValue=value)

    elif phase in D01_LOCKED:
        model = ReadAsmModel(document)
        part = model.ChildDocument
        output = SelfFileInput(str(PureWindowsPath(destination).with_name(model.ChildValue.name + ".SLDPRT")), epoch)
        lights = read_intents(request["lights"], epoch)
        scene = request["scene"]

        def build(value):
            return PrepCylChild(part, output, scene, lights, LabelValue=value).CandidateValue

    else:
        raise ValueError("unknown neutral label proof profile")

    GetDocumentCaps(part)
    _ = PlanCircle(part, Measured=True)
    attempts = proof_guard()
    generated = {name: build(value).BytesValue for name, value in
                 (("default", None), ("on_plane", planar), ("off_plane", label))}
    if phase in D01_LOCKED:
        bundle = PrepCylAsm(document, destination, epoch, scene, lights, LabelValue=label)
        require(bundle.ChildValue.BytesValue == generated["off_plane"],
                "internal assembly preparation did not preserve the child label")
    else:
        bundle = None
    refusals = refusal_checks(build, label, part.feature_timeline[0].parameter_ids[0])
    require(not attempts, "radial label worker accessed external state")
    return {
        "archives": {role: b64encode(data).decode("ascii") for role, data in generated.items()},
        "refusals": refusals,
        "guarded_runtime_accesses": len(attempts),
        "ordinary_assembly_child_identical": bundle is not None,
    }


def frozen_request(disclosure, phase, epoch):
    if phase == "RightContrast":
        name = "IndependentRightLabel"
        part = make_document(name, "Right Plane", (2.175, -3.915), 6.483, 17.542,
                             "diameter", ExtrudeEnd.KMidPlane, False, None)
        label = RadialLabelIn(part.sketches[0].id, part.sketches[0].parameter_ids[0],
                              (0.01352, -0.00735, -0.000817))
        return (
            {"document": ToData(part), "phase": phase, "label": asdict(label), "written_at": epoch,
             "destination": str(PureWindowsPath(r"C:\KitRadialLabel") / (name + ".SLDPRT"))},
            None, None,
        )
    root = disclosure / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(root / "lock.json", LOCK))
    author = json.loads(checked(root / "author.json", AUTHOR))
    pins = D01_LOCKED[phase]
    require(lock["source_locked"] and not lock["heldout_source_locked"] and author["result"]["passed"]
            and tuple(lock["native_artifacts"][phase.lower()][role]["sha256"] for role in ("parent", "child")) == pins,
            "source label displacement lacks its disclosed input custody")
    parent, raw, shape = source_case(root / "Native" / phase, *FILES, pins)
    before = json_digest(parent), json_digest(shape.child)
    projected = project_d01(parent, raw, shape)
    source = owned_label(shape.native.LinkValue)
    require(shape.design_axis == (0.0, 0.0, 1.0) and shape.reference_direction == (1.0, 0.0, 0.0)
            and shape.centers[0][2] == 0.0 and source["mode"] == "radius",
            "source world pose does not support the direct Front sketch frame transform")
    sketch = projected.child.document.sketches[0]
    label = RadialLabelIn(sketch.id, sketch.parameter_ids[0], source["text"])
    require(before == (json_digest(parent), json_digest(shape.child)), "source-to-neutral label changed its original design")
    return (
        {"document": ToData(projected.document), "phase": phase, "label": asdict(label), "written_at": epoch,
         "destination": str(PureWindowsPath(r"C:\KitRadialLabel") / phase / FILES[0]),
         "scene": projected.child.scene, "lights": [light_values(row) for row in projected.child.lights]},
        source,
        dict(zip(("parent", "child"), pins, strict=True)),
    )


def close_rows(left, right):
    return all(isclose(a, b, rel_tol=1e-14, abs_tol=1e-15) for a, b in zip(left, right, strict=True))


def compare(request, source, result):
    payloads = {role: b64decode(data, validate=True) for role, data in result["archives"].items()}
    labels = {
        role: owned_label(ReadNativeLink(SldprtArchive.from_bytes(data), 0))
        for role, data in payloads.items()
    }
    baseline, on_plane, off_plane = (labels[key] for key in ("default", "on_plane", "off_plane"))
    first, second, normal = request["label"]["TextPoint"]
    if source is None:
        fixed = (2.175 * 0.001, -3.915 * 0.001)
        prediction = normal, second, -first
        no_normal = 0.0, second, -first
        radius = 6.483 * 0.001
    else:
        fixed = source["centre"][:2]
        prediction = source["text"]
        no_normal = first, second, 0.0
        radius = source["radius_or_diameter_m"]
    radial_delta = first - fixed[0], second - fixed[1]
    along = hypot(*radial_delta)
    require(off_plane["text"] == prediction and on_plane["text"] == no_normal and off_plane["text"] != baseline["text"],
            "typed display does not contain its exact independently predicted three-dimensional text position")
    require(close_rows(off_plane["direction"], (*[axis / along for axis in radial_delta], 0.0))
            and isclose(off_plane["radial_scale"], along / radius, rel_tol=1e-14)
            and isclose(off_plane["radial_offset"], along - radius, rel_tol=1e-14),
            "normal label motion affected the planar radial leader or its independent radii")
    if source:
        require(close_rows(off_plane["direction"], source["direction"])
                and off_plane["radial_scale"] == source["radial_scale"]
                and off_plane["radial_offset"] == source["radial_offset"]
                and off_plane["centre"] == off_plane["second_centre"] == source["centre"] == source["second_centre"]
                and off_plane["radius_or_diameter_m"] == source["radius_or_diameter_m"]
                and off_plane["depth_mm"] == source["depth_mm"],
                "generated label changes the source scoped radial engine or driving values")
    require({key: value for key, value in on_plane.items() if key != "text"}
            == {key: value for key, value in off_plane.items() if key != "text"}
            and all(baseline[key] == off_plane[key] for key in
                    ("driver_name", "mode", "radius_or_diameter_m", "depth_mm", "dimension_id", "display_index", "parameter_index")),
            "normal motion changed exact typed view or driver ownership")
    stream_differences = {
        role: changed_streams(payloads[left], payloads[right])
        for role, left, right in (("default_to_spatial", "default", "off_plane"),
                                   ("planar_to_spatial", "on_plane", "off_plane"))
    }
    require(all(values == [KResolvedFeaturesStream] for values in stream_differences.values()),
            "radial annotation changed unrelated archive owners")
    return {**result, "archives": {role: {"sha256": fingerprint(data), "bytes": len(data)}
                                    for role, data in payloads.items()},
            "read_labels": labels, "exact_changed_streams": stream_differences}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--phase", choices=("Source", "Edited", "RightContrast"))
    parser.add_argument("--disclosures", type=Path)
    parser.add_argument("--written-at", type=int)
    args = parser.parse_args()
    if args.worker:
        result = run_worker(json.load(sys.stdin))
    else:
        require(args.phase is not None and args.written_at is not None
                and (args.phase == "RightContrast" or args.disclosures is not None),
                "choose a disclosed or independent phase and explicit generation event")
        request, source, pins = frozen_request(args.disclosures, args.phase, args.written_at)
        encoded = json.dumps(request, sort_keys=True, allow_nan=False).encode()
        argv = (sys.executable, "-I", "-B", __file__, "--worker")
        compared = [json.loads(subprocess.check_output(argv, input=encoded)) for _ in range(2)]
        require(compared[0] == compared[1] and not compared[0]["guarded_runtime_accesses"],
                "independent label builders differed or attempted a runtime read")
        if pins:
            folder = args.disclosures / "ConcentricMateSourcePacket02/Disclosed/D01/Native" / args.phase
            for filename, pin in zip(FILES, pins.values(), strict=True):
                checked(folder / filename, pin)
        result = {
            "base": BASE, "phase": args.phase, "neutral_json_sha256": fingerprint(encoded),
            "source_sha256": pins, "source_typed_view": source, "guarded_workers": len(compared),
            "native_runs": 0, "held_out_reads": 0, "public_admission_claim": False,
            **compare(request, source, compared[0]),
        }
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
