from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose, pi
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckScopedPlainWriter import WriterAudit, reject
from CheckCircleRepub import check_republish

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
EPOCH = 1794974400
NAME = "SDK circle diameter beta"
LOCATOR = rf"C:\KitSdkCandidates\{NAME}.SLDPRT"
MANIFEST = ROOT / "re/solidworks/measurements/2026/SdkCircleNative01.json"
MANIFEST_SHA = "bc49ba2f4fd8215f2772c16dc7bdfc7c973f2dcacc4214b4890ef2bdb8ad6be0"
REQUEST_SHA = "e052606918f83ff902a154bd428e1dbab8646092f777ce9eab31d68d97685eb2"


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def check_custody(directory, receipt):
    files = {
        "raw_result_sha256": "Inspection/Inspection.json",
        "packet_sha256": "InspectionJob.json",
        "host_report_sha256": "HostResult.json",
        "postflight_sha256": "NativePostflight.csv",
    }
    for field, name in files.items():
        demand(digest((directory / name).read_bytes()) == receipt[field],
               f"disclosed native evidence changed: {name}")
    terminal = json.loads((directory / files["raw_result_sha256"]).read_bytes())
    demand(terminal["passed"] and terminal["controls_healthy"] and terminal["control_immutable"]
           and terminal["job_sha256"] == receipt["packet_sha256"],
           "native terminal did not complete the disclosed lifecycle")


def check_strict(raw):
    from convert import open_document

    model = open_document(raw, source_format=FORMAT)
    typed = open_document(raw, source_format=FORMAT, include_brep=False)
    demand((model.sketches, model.parameters, model.feature_timeline) ==
           (typed.sketches, typed.parameters, typed.feature_timeline)
           and typed.brep is None and model.brep is not None
           and not model.brep_payloads
           and all(row.code == "sldprt.native_record_unresolved" for row in model.diagnostics)
           and model.diagnostics == typed.diagnostics,
           "default analytic and explicit semantic-only read disagree")
    sketch, = model.sketches
    circle, = sketch.entities
    radial, fixed = sketch.constraints
    profile, boss = tuple(feature for feature in model.feature_timeline if feature.sketch_id == sketch.id)
    diameter, depth = tuple(next(row for row in model.parameters if row.id == feature.parameter_ids[0])
                            for feature in (profile, boss))
    demand(sketch.closed_profile_entity_ids == ((circle.id,),)
           and sketch.parameter_ids == (diameter.id,)
           and (circle.kind, radial.kind, fixed.kind) == ("circle", "diameter", "fixed")
           and ((radial.references[0].entity_id, radial.references[0].point, radial.parameter_id),
                (fixed.references[0].entity_id, fixed.references[0].point, fixed.parameter_id)) ==
               ((circle.id, "", diameter.id), (circle.id, "center", None))
           and circle.attributes["native_center_permanent_mark"] > 0
           and (diameter.owner_id, depth.owner_id) == (profile.id, boss.id)
           and (diameter.name, depth.name, diameter.value.unit, depth.value.unit) == ("D1", "D1", "mm", "mm")
           and (diameter.value.value, depth.value.value) == (22.95, 17.825)
           and boss.definition.length == depth.value
           and str(boss.definition.end_condition) == "blind"
           and str(boss.operation) == "create",
           "public read lost an actual radial relation or editable D1 owner")
    body, = model.bodies
    top = body.topology
    demand(top is not None and top.solid_count == 1 and top.face_count == 3
           and body.final_feature_id == boss.id,
           "cylinder is missing the actual single-body topology")
    measured = (top.volume, top.surface_area, *body.attributes["solidworks.body_centroid_mm"])
    predicted = (pi * 11.475**2 * 17.825, 2 * pi * 11.475 * (11.475 + 17.825), 7.125, -5.675, 8.9125)
    demand(all(isclose(observed, expected, rel_tol=1e-12) for observed, expected in zip(measured, predicted)),
           "cold cylinder analytic measurements differ from its neutral inputs")
    return {"solid_count": top.solid_count, "face_count": top.face_count,
            "volume_mm3": top.volume, "area_mm2": top.surface_area, "centroid_mm": list(measured[2:]),
            "driver_ids": [diameter.id, depth.id]}


def use_combined_edit_for_radial(report):
    snapshots = report["cases"][1]["stages"][1]["snapshots"]
    snapshots["edited_snapshot"] = snapshots["edited_body_snapshot"]


def publication(target, audit, model, evidence, prepared, expected):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    values = {OPTION: evidence, "final_destination": LOCATOR, "require_native_transfers": True}
    direct_writer = SldprtWriter()
    emit = lambda doc, sink, settings: direct_writer.write(doc, sink, WriteOptions(values=settings))
    registry = lambda doc, sink, settings: write_document(
        doc, sink, destination_format=FORMAT, allow_carrier=False, overwrite=True, values=settings)
    exact = digest(prepared) == expected
    if not exact and "zlib-ng" not in ZLIB_RUNTIME_VERSION:
        raise ValueError("canonical compressor changed the measured whole archive")

    opened = audit.target_opens
    results = []
    host_path = os.name != "nt"
    if exact:
        direct, stream = BytesIO(), BytesIO()
        results.extend((emit(model, direct, values), registry(model, stream, values)))
        if host_path:
            results.append(registry(model, target, values))
        else:
            reject(lambda: registry(model, target, values), ValueError, "no unique exact native measurement")
        demand(direct.getvalue() == stream.getvalue() == prepared and audit.target_opens == opened + int(host_path)
               and all(row.vendor_loadable and row.application_usable and row.bytes_written == len(prepared)
                       and row.metadata[OPTION]["generated_sha256"] == expected for row in results)
               and all(len(row.native_capabilities) == 6 for row in results[1:]),
               "exact receipt did not bind normal direct and registry publication")
    else:
        for call in (emit, registry):
            sink = BytesIO()
            reject(lambda: call(model, sink, values), ValueError, "no unique exact native measurement")
            demand(not sink.getvalue(), "unmeasured compressor mutated caller stream")
        reject(lambda: registry(model, target, values), ValueError, "no unique exact native measurement")

    opened = audit.target_opens
    refusals = []
    for label, edit, cause in (
        ("build", lambda report: report["oracle"].update(version="34.0.0.0"), "passing native batch"),
        ("control", lambda report: report["controls"][0].update(healthy=False), "unhealthy native control"),
        ("warning", lambda report: report["cases"][1]["stages"][0].update(open_warnings=1), "staged open"),
        ("reopen", lambda report: report["cases"][1]["stages"][2].update(source_sha256="e" * 64), "staged open"),
        ("driver", lambda report: report["cases"][1]["stages"][1]["radial_edit"].update(name="D1@Boss-Extrude1"), "persisted edit"),
        ("radial_only", use_combined_edit_for_radial, "radial-only edit"),
        ("stream", lambda report: report["cases"][1]["streams"]["Contents/Config-0"].update(sha256="e" * 64), "different typed stream"),
    ):
        changed = deepcopy(evidence)
        edit(changed["receipt"])
        sink = BytesIO()
        reject(lambda: emit(model, sink, values | {OPTION: changed}), ValueError,
               cause if exact or label in ("build", "control") else "no unique exact native measurement")
        demand(not sink.getvalue(), "forged receipt mutated its stream")
        refusals.append(label)
    reject(lambda: registry(model, target, {"final_destination": LOCATOR}), ValueError, "requires an offline native measurement receipt")
    boss, = model.feature_timeline
    depth, radial = model.parameters
    new_depth = replace(depth.value, value=18.5)
    altered = replace(model, parameters=(replace(depth, value=new_depth), radial),
                      feature_timeline=(replace(boss, definition=replace(boss.definition, length=new_depth)),))
    reject(lambda: registry(altered, target, values), ValueError, "no unique exact native measurement")
    if exact:
        for call in (emit, registry):
            sink = BytesIO(b"keep caller bytes")
            sink.seek(4)
            reject(lambda: call(model, sink, values), ValueError, "empty seekable binary stream")
            demand(sink.getvalue() == b"keep caller bytes" and sink.tell() == 4, "native stream refusal changed state")
    demand(audit.target_opens == opened, "a refusal opened a publication output")
    return len(results), [*refusals, "unmeasured_input", "changed_depth", *("occupied_sink",) * exact]


def check_inferred_format(model, directory):
    from convert import write_document
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from convert.api.ApiContext import GetRegistry

    sketch, = model.sketches
    changed = replace(model, sketches=(replace(sketch, parameter_ids=("parameter/missing",)),))
    changed.assert_valid()
    writer = SldprtWriter()
    sink = BytesIO()
    demand(not writer.supports(changed, sink), "SOLIDWORKS claimed a missing sketch driver")
    with TemporaryDirectory(dir=directory) as scratch:
        target = Path(scratch) / "Probe.json"
        target.write_bytes(b"keep existing JSON")
        registry = GetRegistry()
        selected = registry.PickWriter(changed, target).info.FormatId
        demand(selected == registry.PickWriter(model, target).info.FormatId and selected != FORMAT,
               "a missing SOLIDWORKS driver blocked the inferred format")
        reject(lambda: write_document(changed, target, overwrite=True), ValueError, "missing parameter bindings")
        demand(target.read_bytes() == b"keep existing JSON" and not sink.getvalue(),
               "the shared native-state guard touched a destination")


def worker(document, directory):
    sys.path.insert(0, str(ROOT / "src"))
    target = directory / (NAME + ".SLDPRT")
    report_data = MANIFEST.read_bytes()
    demand(digest(report_data) == MANIFEST_SHA, "native report changed")
    receipt = json.loads(report_data)
    case, = (row for row in receipt["cases"] if row["name"] == NAME)
    target.write_bytes(b"keep previous path")
    audit = WriterAudit(ROOT / "src", target)
    sys.addaudithook(audit.observe)

    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from interchange.document.Models.DocumentModel import CadDocument

    for name in (
        "convert.api",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    model = CadDocument.from_json(json.dumps(document))
    settings = WriteOptions(values={"final_destination": LOCATOR})
    audit.phase = "write"
    try:
        prepared = tuple(PrepareNative(model, BytesIO(), EPOCH, settings).BytesValue for _ in range(2))
        demand(prepared[0] == prepared[1], "stateless generation is not deterministic")
        payload = prepared[0]
        output_count, refusals = publication(
            target, audit, model, {"written_at": EPOCH, "receipt": receipt}, payload, case["candidate_sha256"])
    finally:
        audit.phase = "done"

    demand(not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "writer imported a CAD runtime")
    archive = SldprtArchive.from_bytes(payload)
    stream_evidence = {name: (len(value), digest(value)) for name, value in archive.streams.items()}
    demand(stream_evidence == {name: (row["bytes"], row["sha256"]) for name, row in case["streams"].items()}
           and len(stream_evidence) == 10 and not audit.denied,
           "generated logical stream facts or runtime audit are wrong")
    demand(tuple(directory.iterdir()) == (target,)
           and target.read_bytes() == (payload if output_count == 3 else b"keep previous path"),
           "refused publication touched its destination or left staging")
    readback = check_strict(payload)
    repeated = check_republish(target, audit, payload, receipt, EPOCH, LOCATOR, case["candidate_sha256"])
    check_inferred_format(model, directory)
    return {"schema": "kit.sw2026.measured-circle-main.v1", "sha256": digest(payload),
            "receipt_sha256": MANIFEST_SHA, "bytes": len(payload), "stream_count": len(stream_evidence),
            "standalone_publications": output_count, "runtime_input_file_reads": len(audit.denied),
            "profile_owners_verified": True, "strict_readback": readback, "refusals": refusals,
            "strict_republication": repeated,
            "missing_radial_driver_inferred_json": True, "compressor": ZLIB_RUNTIME_VERSION}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        with TemporaryDirectory(prefix="KitCircleMeasured") as directory:
            print(json.dumps(worker(json.load(sys.stdin), Path(directory).resolve()), sort_keys=True))
        return
    demand(args.request is not None and args.original is not None and args.output is not None,
           "host evidence requires the disclosed request, comparison and new receipt")
    request = args.request.read_bytes()
    demand(digest(request) == REQUEST_SHA, "exact disclosed neutral request changed")
    case = json.loads(request)
    demand(case["created_at"] == EPOCH, "disclosed creation event changed")
    data = MANIFEST.read_bytes()
    demand(digest(data) == MANIFEST_SHA, "native report changed")
    check_custody(args.request.parent.parent, json.loads(data))
    child = subprocess.run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                           input=json.dumps(case["document"]), text=True, capture_output=True, check=False)
    demand(child.returncode == 0, child.stdout + child.stderr)
    result = json.loads(child.stdout)
    expected_publications = 2 + int(os.name != "nt")
    demand(result["standalone_publications"] == expected_publications
           and digest(args.original.read_bytes()) == result["sha256"], "disclosed whole-file comparison differs")
    result["tool_sha256"] = digest(HERE.read_bytes())
    result["republication_tool_sha256"] = digest(HERE.with_name("CheckCircleRepub.py").read_bytes())
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"measured circle {result['sha256']}, proof {digest(args.output.read_bytes())}")


if __name__ == "__main__":
    main()
