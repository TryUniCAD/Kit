from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose, pi
from pathlib import Path
from subprocess import run
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent)]
FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
NATIVE_RECORD = ROOT / "re/solidworks/measurements/2026/TwoStockColdNative01.json"
NATIVE_SHA = "d672ec1f8d427844410a7e2d809bfbcf0d130ecaf1df1bb78cefdd1f5f64e187"
DISCLOSED = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def strict_read(raw, authored, receipt, alternate):
    from convert import open_document

    model = open_document(raw, source_format=FORMAT, strict=True, configuration="Default")
    model.assert_valid()
    need(model.brep is not None and not model.brep_payloads and len(model.feature_timeline) == 23,
         "typed cold history or its generated geometry was lost")
    operations = tuple(row for row in model.feature_timeline if row.operation is not None)
    steady, moving, cut = operations
    selection, = model.selections
    profiles = {row.id: row for row in model.sketches}
    need(tuple((row.name, row.operation) for row in operations) ==
         tuple((row.name, row.operation) for row in authored.feature_timeline)
         and steady.input_feature_ids == (steady.sketch_id.replace(":sketch:", ":feature:"),)
         and moving.input_feature_ids == (moving.sketch_id.replace(":sketch:", ":feature:"),)
         and cut.input_feature_ids == (steady.id, cut.sketch_id.replace(":sketch:", ":feature:"))
         and cut.selection_ids == (selection.id,) and not steady.selection_ids and not moving.selection_ids
         and len(selection.path) == 1 and selection.path[0].entity_kind == "feature"
         and selection.path[0].entity_id == steady.id and selection.path[0].subelement == "body"
         and cut.definition.end_condition == "through_all" and cut.definition.length is None
         and cut.definition.direction == authored.feature_timeline[-1].definition.direction
         and not cut.definition.reversed and not cut.parameter_ids,
         "the explicit signed through end or actual selected body was lost")
    need(tuple(tuple(r.kind for r in profiles[row.sketch_id].constraints) for row in (steady, moving))
         == (("horizontal", "vertical", "horizontal", "vertical"),) * 2
         and not profiles[cut.sketch_id].constraints
         and profiles[cut.sketch_id].support_plane_id == profiles[steady.sketch_id].support_plane_id
         != profiles[moving.sketch_id].support_plane_id,
         "the stock and free circular profiles did not retain their real support owners")
    drivers = {row.owner_id: row for row in model.parameters}
    need(len(drivers) == 2 and len(model.parameters) == 2
         and all(drivers[row.id].id == row.parameter_ids[0]
                 and drivers[row.id].value == row.definition.length
                 and drivers[row.id].name == "D1" for row in (steady, moving))
         and tuple(drivers[row.id].value.value for row in (steady, moving))
         == tuple(row.value.value for row in authored.parameters),
         "an independent editable stock D1 did not survive")
    need(tuple(row.final_feature_id for row in model.bodies) == (moving.id, cut.id)
         and {body.design_body_id for body in model.brep.bodies} == {body.id for body in model.bodies},
         "the solved solids did not retain two separate result owners")
    shapes = [
        {"faces": row.topology.face_count, "volume": row.topology.volume, "area": row.topology.surface_area,
         "center": list(row.attributes["solidworks.body_centroid_mm"])}
        for row in model.bodies
    ]
    if alternate:
        expected = (14 * 11 * 31.875, (28 * 14 - pi * 2.375**2) * 13.625)
        need(tuple(row["faces"] for row in shapes) == (6, 7)
             and all(isclose(row["volume"], value, rel_tol=1e-12)
                     for row, value in zip(shapes, expected, strict=True)),
             "neutral enclosed cut failed its independent analytic geometry")
    else:
        expected = receipt["snapshots"]["initial"]["bodies"]
        for row, native in zip(shapes, (expected[moving.name], expected[steady.name]), strict=True):
            for value, observed in zip(
                (row["volume"], row["area"], *row["center"]),
                (native["volume_mm3"], native["area_mm2"], *native["centre_mm"]),
                strict=True,
            ):
                need(isclose(value, observed, rel_tol=5e-7, abs_tol=1e-8),
                     f"analytic body differs from native observation: {value} versus {observed}")
        need(tuple(row["faces"] for row in shapes) == (6, 8), "side breakout topology changed")
    return {"rows": len(model.feature_timeline), "driver_ids": [drivers[row.id].id for row in (steady, moving)],
            "selected_producer": steady.id, "cut_id": cut.id, "solids": shapes}


def cross_owner(raw):
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdOwners import ReadColdOwners
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.FromBytes(raw)
    link = ReadNativeLink(archive, 0)
    owners = ReadColdOwners(link)
    owners.WrapperValue.FieldsValue["f108"] = owners.StockValues[1].NodeValue.FieldsValue["f08"]
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    edited, _ = WriteResolMut(link.ResolvedValue.RootsValue, None, 19000,
                              link.ConfigValue.MapValue, MakeLinkContext(link.ConfigValue, manager))
    return BuildSldprt(dict(archive.streams) | {link.StreamName: edited}, FormatVersion=4)


def guarded_write(model, altered, receipt, directory):
    from CheckScopedPlainWriter import WriterAudit, reject
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import PrepStockPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from SelectedStockModel import EPOCH, LOCATOR, NAME

    for name in ("interchange.brep.Validation.BrepValidate",
                 "interchange.document.Behavior.DocumentIo",
                 "interchange.document.Models.DocumentProvenance",
                 "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Validation.DocumentFeatureValidate",
                 "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(name)
    for name in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(name)

    path = directory / f"{NAME}.SLDPRT"
    path.write_bytes(b"preserve existing path")
    stream_path = directory / "owned-stream.bin"
    values = {"final_destination": LOCATOR, OPTION: {"written_at": EPOCH, "receipt": receipt}}
    audit = WriterAudit(ROOT / "src", path)
    emit = SldprtWriter().write

    def direct(document, target, options=values):
        return emit(document, target, WriteOptions(values=options, overwrite=True))

    def registry(document, target, options=values):
        return write_document(document, target, destination_format=FORMAT, overwrite=True, values=options)

    failures = {}
    with stream_path.open("xb") as file_sink:
        sys.addaudithook(audit.observe)
        audit.phase = "write"
        try:
            settings = WriteOptions(values={"final_destination": LOCATOR})
            first, second = (
                PrepStockPart(model, BytesIO(), EPOCH, settings) for _ in range(2)
            )
            need(first == second, "pure composition changed between invocations")
            unrelated = altered.metadata["name"]
            other = PrepStockPart(altered, BytesIO(), EPOCH, WriteOptions(values={
                "final_destination": rf"C:\KitSdkCandidates\{unrelated}.SLDPRT"
            }))
            if digest(first.BytesValue) != DISCLOSED:
                need("zlib-ng" in ZLIB_RUNTIME_VERSION, "canonical compressor changed measured bytes")
                for route in (direct, registry):
                    sink = BytesIO()
                    reject(lambda: route(model, sink), ValueError, "no exact native measurement")
                    need(sink.getvalue() == b"", "different compressed bytes acquired native claims")
                return first, other, failures, 0, audit.denied, audit.target_opens

            for route in (direct, registry):
                sink = BytesIO()
                result = route(model, sink)
                need(sink.getvalue() == first.BytesValue and result.bytes_written == 8574
                     and result.vendor_loadable and result.application_usable
                     and result.metadata[OPTION]["generated_sha256"] == DISCLOSED,
                     "direct and registry routes did not bind the actual measured archive")
            file_result = registry(model, file_sink)
            need(file_result.bytes_written == 8574 and file_result.application_usable,
                 "write-only file sink did not report exact measured publication")

            for route in (direct, registry):
                occupied = BytesIO(b"preserve caller prefix")
                occupied.seek(5)
                failures["occupied_sink"] = reject(lambda: route(model, occupied), ValueError, "empty seekable binary stream")
                need(occupied.getvalue() == b"preserve caller prefix" and occupied.tell() == 5,
                     "whole-file refusal changed caller state")
                for field in ("build", "control"):
                    changed = deepcopy(values)
                    summary = changed[OPTION]["receipt"]["summary"]
                    if field == "build":
                        summary["oracle_build"] = "34.0.0.0"
                    else:
                        summary["phases"]["Before"]["passed"] = False
                    sink = BytesIO()
                    failures[field] = reject(lambda: route(model, sink, changed), ValueError, "exact controlled native receipt")
                    need(not sink.getvalue(), "rewritten receipt wrote bytes")
                sink = BytesIO()
                failures["missing_receipt"] = reject(lambda: route(model, sink, {}),
                    ValueError, "requires an offline native measurement receipt")
                failures["wrong_logical_locator"] = reject(
                    lambda: route(model, sink, values | {"final_destination": r"C:\Unmeasured\GeneratedTwoStockGraph01.SLDPRT"}),
                    ValueError, "exact measured locator")
                first_stock, moving_stock, cut = model.feature_timeline
                first_drive, moving_drive = model.parameters
                longer = replace(moving_drive.value, value=29.0)
                changed_model = replace(model,
                    parameters=(first_drive, replace(moving_drive, value=longer)),
                    feature_timeline=(first_stock,
                        replace(moving_stock, definition=replace(moving_stock.definition, length=longer)), cut))
                failures["changed_model"] = reject(lambda: route(changed_model, sink),
                    ValueError, "no exact native measurement")
                failures["wrong_physical_locator"] = reject(lambda: route(model, path), ValueError, "actual measured final path")
                need(not sink.getvalue(), "a rejected publication modified its empty sink")

            failures["cross_target_depthless"] = reject(
                lambda: write_document(model, BytesIO(), destination_format="interchange.json"),
                ValueError, "depthless extrusion reconstruction is unqualified")
        finally:
            audit.phase = "done"
    need(path.read_bytes() == b"preserve existing path" and stream_path.read_bytes() == first.BytesValue
         and set(directory.iterdir()) == {path, stream_path}, "path refusal changed destination or left stage")
    return first, other, failures, 3, audit.denied, audit.target_opens


def worker():
    from CheckScopedPlainWriter import reject
    from CheckStockRoundTrip import check_preserved
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.document.Models.DocumentModel import CadDocument
    from SelectedStockModel import selected_stock_document

    raw = NATIVE_RECORD.read_bytes()
    need(digest(raw) == NATIVE_SHA, "the tracked disclosed receipt changed")
    receipt = json.loads(raw)
    request = json.load(sys.stdin)
    model = CadDocument.from_json(json.dumps(request))
    varied = selected_stock_document(alternate=True)
    with TemporaryDirectory(prefix="KitSelectedStockWriter") as saved:
        first, other, refusals, outputs, denied, opens = guarded_write(
            model, varied, receipt, Path(saved).resolve()
        )
        roundtrip = Path(saved).resolve() / "Roundtrip"
        roundtrip.mkdir()
        readback = check_preserved(first.BytesValue, first, receipt, DISCLOSED, roundtrip)
    need(not denied and not opens
         and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
         "a model-only generation accessed external content or a CAD runtime")
    archives = [SldprtArchive.FromBytes(value.BytesValue) for value in (first, other)]
    results = []
    for archive, candidate, neutral, alternate in zip(
        archives, (first, other), (model, varied), (False, True), strict=True
    ):
        need(archive.streams == candidate.StreamsValue and len(archive.streams) == 10,
             "container differs from its generated stream owners")
        results.append({
            "sha256": digest(candidate.BytesValue), "bytes": len(candidate.BytesValue),
            "streams": {name: {"bytes": len(data), "sha256": digest(data)}
                        for name, data in sorted(archive.streams.items())},
            "strict": strict_read(candidate.BytesValue, neutral, receipt, alternate),
        })
    need(results[0]["streams"]["swXmlContents/KeyWords"]["bytes"]
         != results[1]["streams"]["swXmlContents/KeyWords"]["bytes"],
         "unrelated named model did not change stream length")
    wrong = cross_owner(first.BytesValue)
    refusals["crossed_typed_selector"] = reject(
        lambda: open_document(wrong, source_format=FORMAT, strict=True),
        ValueError, "Parasolid payload")
    return {"schema": "kit.sw2026.measured-selected-stock-sdk.v1", "cases": results,
            "publications": outputs, "runtime_input_file_reads": len(denied), "staged_output_opens": opens,
            "receipt_sha256": NATIVE_SHA, "refusals": refusals, "compressor": ZLIB_RUNTIME_VERSION,
            "readback_roundtrip": readback}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--comparison", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(), sort_keys=True))
        return
    from SelectedStockModel import selected_stock_document

    request = selected_stock_document().to_json()
    completed = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                    input=request, capture_output=True, text=True, check=False, timeout=90)
    need(completed.returncode == 0, completed.stdout + completed.stderr)
    report = json.loads(completed.stdout)
    if args.comparison is not None:
        from convert.adapters.solidworks.Container.Container import SldprtArchive

        measured = args.comparison.read_bytes()
        archive = SldprtArchive.FromBytes(measured)
        exact = report["cases"][0]
        need(digest(measured) == exact["sha256"] == DISCLOSED
             and {name: {"bytes": len(data), "sha256": digest(data)}
                  for name, data in archive.streams.items()} == exact["streams"],
             "independent archive or one of its ten streams differs from regenerated output")
        report["compared_all_disclosed_streams"] = True
    report["tool_sha256"] = digest(HERE.read_bytes())
    report["neutral_tool_sha256"] = digest(HERE.with_name("SelectedStockModel.py").read_bytes())
    report["readback_tool_sha256"] = digest(HERE.with_name("CheckStockRoundTrip.py").read_bytes())
    result = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
