from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyOriginalFcstdAttachedBox import (
    CASE,
    FORMAT,
    LOCATOR,
    NATIVE_SHA,
    ROOT,
    SOURCE_SHA,
    digest,
    guarded,
    locked,
    prewarm,
    refusal,
    require,
    source_proof,
    target_read,
)
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import PlanAttachedBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import PlanImportPart
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument


BASE = "1e19fb4268e5e689402d0ffbf82ae3e4d4084058"
ORIGIN_SHA = "2f0e5e20da3e8f6d2073a7c8dd654b0c5035ed142c2e0392a14de832cd82eb5d"
ORIGIN_RECEIPT_SHA = "a28e15c906255d21bc2b7304539c1a3cd5445b2092c1570c897f73636750baa6"
SENTINEL = b"unchanged caller data"


def intake(path, expected):
    raw = locked(path, expected)
    model = open_document(path, strict=True)
    wire = model.to_json(indent=None)
    portable = CadDocument.from_json(wire)
    require(portable == model and portable.source.sha256 == expected,
            "strict FCStd source did not survive ordinary neutral JSON")
    return portable, raw


def changed_drivers(model):
    feature, = model.feature_timeline
    length, width, visible = (
        next(row for row in model.parameters if row.attributes["freecad_path"] == key)
        for key in ("Length", "Width", "Visibility")
    )
    caption = replace(width, name="unowned Width caption")
    visibility = replace(visible, value=replace(visible.value, value=not visible.value.value))
    renamed = replace(length, id="foreignLength")
    changed_feature = replace(feature, parameter_ids=tuple(
        renamed.id if key == length.id else key for key in feature.parameter_ids))
    return {
        "independent_driver_caption": replace(model, parameters=tuple(
            caption if row is width else row for row in model.parameters)),
        "independent_visibility": replace(model, parameters=tuple(
            visibility if row is visible else row for row in model.parameters)),
        "coherent_foreign_driver_id": replace(model, feature_timeline=(changed_feature,), parameters=tuple(
            renamed if row is length else row for row in model.parameters)),
    }


def owner_refusals(model, origin):
    docs = changed_drivers(model)
    for alternate in docs.values():
        ReadBoxSource(alternate)
    refusals = {key: refusal(lambda: PlanAttachedBox(value),
                            "FreeCAD attached box neutral owners disagree with its archive")
                for key, value in docs.items()}
    original, binding = NativeDocPair(model)
    other_cache = replace(model.brep_payloads[0], data=model.brep_payloads[2].data,
                          sha256=model.brep_payloads[2].sha256)
    refusals.update({
        "missing_verification_binding": refusal(lambda: PlanAttachedBox(replace(
            model, brep_payloads=tuple(row for row in model.brep_payloads if row is not binding))),
            "FreeCAD attached box has no exact retained document binding"),
        "altered_document_bytes": refusal(lambda: PlanAttachedBox(replace(
            model, brep_payloads=tuple(replace(row, data=row.data + b"changed")
                                       if row is original else row for row in model.brep_payloads))),
            "FreeCAD attached box has no exact retained document binding"),
        "equal_incidence_crossed_cache_owner": refusal(lambda: PlanAttachedBox(replace(
            model, brep_payloads=(other_cache, *model.brep_payloads[1:]))),
            "FreeCAD attached box neutral owners disagree with its archive"),
        "actual_origin_fixed_F14a": refusal(lambda: PlanAttachedBox(origin),
            "FreeCAD primitive uses another attachment engine or owner"),
    })
    return refusals


def publication_refusals(model, part, target):
    writer = SldprtWriter()
    stream = BytesIO(SENTINEL)
    stream.seek(3)
    opts = {"final_destination": LOCATOR, "require_native_transfers": True}
    native = ("native-only feature definitions cannot be exported: " + model.source.path
              + ": freecad:feature:AdditiveBox (freecad.fcstd:PartDesign::AdditiveBox)")
    findings = {
        "inferred_import_profile": refusal(lambda: PlanImportPart(model, target),
            "bare local import requires a neutral millimetre B-rep"),
        "plain_route_for_projected_source_identity": refusal(lambda: PlanNativePart(part.ModelValue),
            "plain part preparation does not admit unresolved or extended source state"),
    }
    try:
        write_document(model, target, overwrite=True, allow_carrier=False, values=opts)
    except NotFoundError as error:
        require(str(error) == "no writer supports the destination", "wrong inferred refusal")
        findings["inferred_path"] = str(error)
    else:
        raise ValueError("intact source reached inferred public writing")
    for label, sink in (("explicit_path", target), ("explicit_stream", stream)):
        findings[label] = refusal(lambda: write_document(
            model, sink, destination_format=FORMAT, overwrite=True, allow_carrier=False,
            values=opts), native).replace(model.source.path, "{actual source locator}")
    for label, sink in (("direct_path", target), ("direct_stream", stream)):
        findings[label] = refusal(lambda: writer.write(
            model, sink, WriteOptions(overwrite=True, values=opts)), native).replace(
                model.source.path, "{actual source locator}")
    require(stream.getvalue() == SENTINEL and stream.tell() == 3, "caller stream changed on refusal")
    return {"refusals": findings, "published_bytes": 0, "sink_state_preserved": True,
            "missing_static_caps": sorted(cap.value for cap in GetDocumentCaps(model) - writer.info.Capabilities)}


def build(request):
    path, origin_path = (Path(request[key]) for key in ("attached", "origin"))
    model, raw = intake(path, SOURCE_SHA)
    origin, _ = intake(origin_path, ORIGIN_SHA)
    prewarm()
    with TemporaryDirectory(prefix="KitIntactAttachedPlan.") as folder:
        target = Path(folder) / "F14c.SLDPRT"
        target.write_bytes(SENTINEL)
        with guarded():
            source = source_proof(model, raw)
            plan = PlanAttachedBox(model)
            part = plan.PartSource
            require(plan.SourceDocument is model and part.ModelValue.source == model.source
                    and part.ModelValue.brep is None and not part.ModelValue.brep_payloads
                    and set(part.ParameterBindings) == {row["source_id"] for row in source["drivers"].values()},
                    "clean construction lost the actual source or editable driver names")
            source_label = replace(model.source, path=path.name)
            retained = replace(plan.SourceDocument, source=source_label).to_json(indent=None)
            cache = {"data": len(NativeDocPair(model)[0].data), "payloads": len(model.brep_payloads),
                     "parameters": len(model.parameters), "source_object_count": len(source["object_owners"])}
            negatives = owner_refusals(model, origin)
            generated = MakeOriginBox(part.ModelValue, LOCATOR, part.CreationEpoch, part.PropertiesValue,
                                      UnitsValue=part.UnitsValue, TopAttached=True)
            denied = publication_refusals(model, part, target)
        require(list(Path(folder).iterdir()) == [target] and target.read_bytes() == SENTINEL,
                "refused conversion left staging entries or replaced the existing destination")
    locked(path, SOURCE_SHA)
    locked(origin_path, ORIGIN_SHA)
    return {"source": source, "original_neutral_preserved": True, "retained_source": cache,
            "retained_neutral_basename_sha256": digest(retained.encode()), "source_sha256": SOURCE_SHA,
            "source_refusals": negatives, "public_write": denied,
            "creation_epoch": part.CreationEpoch, "editable_bindings": dict(part.ParameterBindings),
            "projected_properties": {"summary": dict(part.PropertiesValue.SummaryFields),
                                     "document": dict(part.PropertiesValue.DocumentFields)},
            "artifact": {"bytes": len(generated.BytesValue), "sha256": digest(generated.BytesValue),
                         "streams": {key: {"bytes": len(value), "sha256": digest(value)}
                                     for key, value in generated.StreamsValue.items()}},
            "candidate_b64": b64encode(generated.BytesValue).decode(), "runtime_data_file_reads": 0}


def worker(mode, request):
    done = subprocess.run([sys.executable, "-I", "-B", str(HERE), mode],
                          input=json.dumps(request), capture_output=True, text=True, timeout=120)
    require(done.returncode == 0 and not done.stderr, done.stderr or "plan process failed")
    return json.loads(done.stdout)


def prior_native_measures(record, target, drivers):
    ordered = ("Length", "Width", "Height")
    initial = [drivers[key]["value_mm"] / 1000 for key in ordered]
    require(initial == record["native_drivers_m"], "live native values disagree with the source")
    snapshots = {"Original": initial}
    for index, (name, value) in enumerate(zip(ordered,
                                               record["independent_edit_values_m"], strict=True)):
        edited = list(initial)
        edited[index] = value
        snapshots[name] = edited
    for name, (length, width, height) in snapshots.items():
        expected = record["fresh_reopen_mass_si"][name]
        actual = (length * width * height, 2 * (length*width + width*height + height*length),
                  length / 2, -height / 2, width / 2)
        require(all(isclose(a, b, rel_tol=2e-7) for a, b in zip(
            actual, (expected["volume"], expected["area"], *expected["com"]), strict=True)),
            f"signed analytic states disagree with measured reopen {name}")
    old = record["fresh_reopen_mass_si"]["Original"]
    require(isclose(target["volume_mm3"] / 1e9, old["volume"], rel_tol=2e-7)
            and isclose(target["area_mm2"] / 1e6, old["area"], rel_tol=2e-7)
            and all(isclose(a / 1000, b, rel_tol=2e-7)
                    for a, b in zip(target["centre_mm"], old["com"], strict=True)),
            "strict target differs from the exact measured native initial state")
    return {"fresh_reopen_snapshots": len(snapshots), "signed_geometry_checks": 25,
            "independent_edits_mm": [value * 1000 for value in record["independent_edit_values_m"]]}


def main():
    if sys.argv[1:] in (["build"], ["read"]):
        lookup("utf-8-sig")
        operation = build if sys.argv[1] == "build" else target_read
        print(json.dumps(operation(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    parser = ArgumentParser()
    parser.add_argument("attached", type=Path)
    parser.add_argument("origin", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    request = {key: str(getattr(args, key).resolve(strict=True)) for key in ("attached", "origin")}
    measures = ROOT / "re/solidworks/measurements/2026"
    native = json.loads(locked(measures / "AttachedTopBoxGeneratedNative01.json", NATIVE_SHA))
    origin = json.loads(locked(measures / "SdkFreecadOriginBoxNative01.json", ORIGIN_RECEIPT_SHA))
    require(native["oracle_file_version"] == "34.5.2.0604" and native["controls_healthy"]
            and native["distinct_native_processes"] == 8 and origin["passed"]
            and origin["controls_healthy"] and origin["source_sha256"] == ORIGIN_SHA,
            "previous disclosed control/source identity changed")
    built = worker("build", request)
    require(built == worker("build", request), "independent intact builds disagree")
    measured = native["cases"][CASE]
    require(measured["input_sha256"] == built["source_sha256"] == SOURCE_SHA
            and built["artifact"] == {"bytes": measured["bytes"], "sha256": measured["output_sha256"],
                                     "streams": measured["streams"]},
            "computed file differs from the previously measured complete archive")
    readback = worker("read", built)
    require(readback == worker("read", built), "independent strict target reads disagree")
    check = prior_native_measures(measured, readback, built["source"]["drivers"])
    del built["candidate_b64"]
    inputs = (HERE, HERE.with_name("VerifyOriginalFcstdAttachedBox.py"), HERE.with_name("BoxIncidence.py"),
              ROOT / "src/convert/adapters/freecad/Native.py",
              ROOT / "src/convert/adapters/solidworks/Core/Preparation/FreecadBox/PlanAttachedBox.py")
    receipt = {"schema": "kit.sw2026.intact-freecad-attached-plan.v1", "sdk_base": BASE, "passed": True,
               **built, "target": readback, "same_native_locator": LOCATOR,
               "prior_native_comparison": check, "prior_native_receipt_sha256": NATIVE_SHA,
               "origin_contrast_source_sha256": ORIGIN_SHA, "prior_origin_receipt_sha256": ORIGIN_RECEIPT_SHA,
               "tool_and_changed_source_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in inputs},
               "fresh_workers": {"guarded_build": 2, "guarded_readback": 2}, "native_processes_started": 0,
               "public_writer_qualified": False, "historical_benchmark_membership_verified": False,
               "source_payload_carrier_emitted": False, "benchmark_conversion_credits": 0}
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(receipt, out, indent=2, sort_keys=True, allow_nan=False)
        out.write("\n")


if __name__ == "__main__":
    main()
