from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyIntactAttachedPlan import intake, publication_refusals, SENTINEL
from VerifyOriginalFcstdAttachedBox import (
    CASE, FORMAT, LOCATOR, NATIVE_SHA, ROOT, SOURCE_SHA, digest, guarded, locked,
    prewarm, refusal, require, xyz,
)
from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import PlanAttachedBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import ReadOriginAxes
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


BASE = "ba956e9b3948fac6ecdeaa0840fece2d19b47bbf"
CLI_ERROR = {
    "error": "ValueError",
    "message": "CapturedObjects records are not conversion-ready; use kit decode or kit research for inspection",
}
BOOTSTRAP = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('convert',run_name='__main__')"


def source_object(model, name):
    row, = (item for item in model.metadata["freecad"]["objects"] if item["name"] == name)
    return row


def replace_owner(model, changed):
    native = model.metadata["freecad"]
    objects = [changed if row["name"] == changed["name"] else row for row in native["objects"]]
    return replace(model, metadata={**model.metadata, "freecad": {**native, "objects": objects}})


def with_value(owner, field, value, *, key="value"):
    properties = owner["properties"]
    property_row = properties[field]
    child, = property_row["children"]
    changed = {**property_row, "children": [{**child, "attributes": {**child["attributes"], key: value}}]}
    return {**owner, "properties": {**properties, field: changed}}


def model_contrasts(model):
    origin, south, north = (source_object(model, name) for name in ("Origin", "Y_Axis", "Z_Axis"))
    labels = with_value(with_value(south, "Label", "Draft direction"), "Visibility", "false")
    changed = replace_owner(model, labels)
    actual = ReadOriginAxes(changed).AxisValues[1]
    require(actual.RoleName == "Y_Axis" and actual.LabelValue == "Draft direction" and not actual.RecordShown,
            "the presented label or model visibility was normalized to a default")
    return {
        "alternate_label_and_visibility_projected": True,
        "unverified_changed_document": refusal(lambda: PlanAttachedBox(changed),
            "FreeCAD attached box neutral owners disagree with its archive"),
        "aliased_source_id": refusal(lambda: ReadOriginAxes(replace_owner(
            model, {**south, "object_id": origin["object_id"]})),
            "FreeCAD origin requires distinct native object identities"),
        "crossed_source_role": refusal(lambda: ReadOriginAxes(replace_owner(
            model, with_value(south, "Role", "Z_Axis"))),
            "FreeCAD property Role is outside the admitted box policy"),
        "invalid_model_visibility": refusal(lambda: ReadOriginAxes(replace_owner(
            model, with_value(south, "Visibility", "unknown"))),
            "FreeCAD origin visibility is malformed"),
        "wrong_axis_angle_despite_unchanged_quaternion": refusal(lambda: ReadOriginAxes(replace_owner(
            model, with_value(south, "Placement", "0.0", key="A"))),
            "FreeCAD origin axis angle disagrees with its stored quaternion"),
        "consistent_but_crossed_placement": refusal(lambda: ReadOriginAxes(replace_owner(model, {
            **south, "properties": {**south["properties"], "Placement": north["properties"]["Placement"]}})),
            "FreeCAD origin axis does not match its owned principal direction"),
    }


def visibility_source(model, raw, origin):
    with ZipFile(BytesIO(raw)) as archive:
        require(archive.namelist() == ["Document.xml", "PartShape.brp", "PartShape1.brp", "PartShape2.brp"],
                "source has a different stored presentation inventory")
    result = {"origin_id": origin.OriginId, "origin_label": origin.OriginLabel,
              "origin_model_visibility": origin.RecordShown, "saved_gui_document_present": False,
              "axes": []}
    basis = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    for axis, expected in zip(origin.AxisValues, basis, strict=True):
        record = source_object(model, axis.RoleName)
        frame = axis.FrameValue
        direction = xyz(frame.x_axis)
        require(axis.RecordId == record["object_id"] and xyz(frame.origin) == (0., 0., 0.)
                and all(isclose(a, b, rel_tol=0, abs_tol=1e-14) for a, b in zip(direction, expected, strict=True))
                and axis.RecordShown, "independent source axis identity or carrier disagrees")
        result["axes"].append({"id": axis.RecordId, "role": axis.RoleName, "label": axis.LabelValue,
                               "origin_mm": xyz(frame.origin), "direction": direction,
                               "model_visibility": axis.RecordShown})
    return result


def target_history(payload, axes):
    doc = open_document(payload, source_format=FORMAT, strict=True)
    link = ReadNativeLink(SldprtArchive.from_bytes(payload), 0)
    roots = IndexFeatures(link)
    axis_names = {item["label"] for item in axes["axes"]}
    axes_in_target = [ReadNativeName(row) for row in roots.values() if row.ClassValue.NameValue == "moRefAxis_c"]
    require(not axes_in_target and not axis_names & {row.name for row in doc.feature_timeline},
            "the measured target datum inventory changed")
    require(len(doc.bodies) == 1 and {row.name for row in doc.support_planes} == {"Front Plane", "Top Plane", "Right Plane"}
            and sum(row.name == "Origin" for row in doc.feature_timeline) == 1,
            "the measured target lost its common body or datum controls")
    return {"root_rows": len(roots), "reference_axis_rows": axes_in_target,
            "missing_selectable_origin_axes": sorted(axis_names), "principal_planes": len(doc.support_planes),
            "bodies": len(doc.bodies)}


def run_cli(source, target, measurement):
    args = [sys.executable, "-I", "-B", "-c", BOOTSTRAP, str(ROOT / "src"), "convert", str(source), str(target),
            "--to", FORMAT, "--native-measurement", str(measurement), "--overwrite", "--json"]
    process = subprocess.run(args, text=True, capture_output=True, timeout=120)
    output = json.loads(process.stderr or process.stdout)
    require(process.returncode == 1 and output == CLI_ERROR, "CLI changed its complete-source refusal")
    return {"exit": process.returncode, **output}


def proof(source, reference):
    model, raw = intake(source, SOURCE_SHA)
    measurement = ROOT / "re/solidworks/measurements/2026/AttachedTopBoxGeneratedNative01.json"
    native = json.loads(locked(measurement, NATIVE_SHA))
    measured = native["cases"][CASE]
    require(native["controls_healthy"] and native["oracle_file_version"] == "34.5.2.0604"
            and measured["input_sha256"] == SOURCE_SHA, "the prior exact native receipt changed")
    lookup("utf-8-sig")
    prewarm()
    with TemporaryDirectory(prefix="KitF14cDatum.") as name:
        destination = Path(name) / "F14c.SLDPRT"
        destination.write_bytes(SENTINEL)
        with guarded():
            plan = PlanAttachedBox(model)
            part = plan.PartSource
            model_axes = visibility_source(model, raw, plan.OriginAxes)
            contrasts = model_contrasts(model)
            built = MakeOriginBox(part.ModelValue, LOCATOR, part.CreationEpoch, part.PropertiesValue,
                                  UnitsValue=part.UnitsValue, TopAttached=True)
            target = target_history(built.BytesValue, model_axes)
            sdk = publication_refusals(model, part, destination)
        cli = run_cli(source, destination, measurement)
        require(destination.read_bytes() == SENTINEL and list(destination.parent.iterdir()) == [destination],
                "refusal mutated a caller path or retained staged files")
    archive = locked(reference, measured["output_sha256"])
    require(built.BytesValue == archive and measured["streams"] == {
        name: {"bytes": len(stream), "sha256": digest(stream)} for name, stream in built.StreamsValue.items()},
        "model-only candidate no longer matches the measured native archive")
    locked(source, SOURCE_SHA)
    preparation = ROOT / "src/convert/adapters/solidworks/Core/Preparation/FreecadBox"
    files = (HERE, preparation / "PlanAttachedBox.py", *(preparation / "Source" / name for name in (
        "BoxOriginAxes.py", "ReadAxisPlace.py", "ReadOriginAxes.py")))
    return {"schema": "kit.sw2026.f14c-public-datum-boundary.v1", "base": BASE, "passed": True,
            "source_sha256": SOURCE_SHA, "prior_native_receipt_sha256": NATIVE_SHA,
            "generated_bytes": len(archive), "generated_sha256": digest(archive),
            "measured_streams_matched": len(built.StreamsValue), "source": model_axes, "target": target,
            "typed_contrasts": contrasts, "sdk_refusals": sdk, "cli_refusal": cli,
            "tool_and_changed_source_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in files},
            "guarded_runtime_data_file_reads": 0, "native_processes_started": 0, "full_source_qualified": False,
            "historical_corpus_membership_verified": False, "benchmark_conversion_credits": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("measured_archive", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = proof(args.source, args.measured_archive)
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
