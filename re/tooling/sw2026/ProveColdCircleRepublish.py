from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from tempfile import TemporaryDirectory
import sys


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(TOOLS)]

from ProveCircleEndPort import DISCLOSED, FORMAT, MEASURE, OutputGuard, digest, preload, report_inputs
from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Circle.IsCircRead import IsCircRead
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle
from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircInput import ReadCircInput
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData


def registry(document, target, values):
    return write_document(document, target, destination_format=FORMAT, allow_carrier=False, values=values)


def adapter(document, target, values):
    return SldprtAdapter().write(document, target, WriteOptions(values=values))


def writer(document, target, values):
    return SldprtWriter().write(document, target, WriteOptions(values=values))


def assert_result(result, source, native_file):
    assert result.vendor_loadable and result.application_usable
    assert not result.carrier_capabilities and not result.dropped
    assert result.native_capabilities == GetDocumentCaps(source)
    assert result.bytes_written == len(native_file)
    assert result.metadata[MEASURE]["generated_sha256"] == digest(native_file)


def refusal(document, sink, values, diagnostic):
    try:
        writer(document, sink, values)
    except ValueError as error:
        assert diagnostic in str(error), (diagnostic, str(error))
        return diagnostic
    raise AssertionError("unverified source reached publication")


def change_centre(source):
    (sketch,) = source.sketches
    circle, point = sketch.entities
    x, y = circle.attributes["native_center_m"]
    changed = replace(circle, attributes={**circle.attributes, "native_center_m": (x, y + 0.00025)})
    return replace(source, sketches=(replace(sketch, entities=(changed, point)),))


def change_driver(source):
    (*previous, driver) = source.parameters
    attributes = {**driver.attributes, "native_value": driver.attributes["native_value"] + 0.004}
    changed = replace(driver, value=replace(driver.value, value=attributes["native_value"] / 0.001),
                      attributes=attributes)
    (body,) = source.bodies
    steps = []
    for step in source.feature_timeline:
        if step.id == body.final_feature_id:
            length = "length" if driver.name == "D1" else "second_length"
            step = replace(step, definition=replace(step.definition, **{length: changed.value}))
        steps.append(step)
    return replace(source, parameters=(*previous, changed), feature_timeline=tuple(steps))


def check_refusals(source, values, no_carrier):
    (body,) = source.bodies
    wrapped = "SOLIDWORKS cold readback differs"
    contrasts = (
        ("stale_centre", change_centre(source), values, "centre disagrees"),
        ("edited_depth", change_driver(source), values, wrapped),
        ("unprojected_record", replace(source, metadata={**source.metadata, "extra_owner": "foreign"}), values, wrapped),
        ("changed_source_digest", replace(source, source=replace(source.source, sha256="0" * 64)), values, wrapped),
        ("changed_body_name", replace(source, bodies=(replace(body, name="Different body"),)), values, wrapped),
        ("missing_source_carrier", no_carrier, values, wrapped),
        ("missing_measurement", source, {key: value for key, value in values.items() if key != MEASURE},
         "offline native measurement"),
        ("wrong_locator", source,
         {**values, "final_destination": values["final_destination"].replace("KitSdkCandidates", "Different")}, wrapped),
    )
    observed = {}
    for label, document, settings, expected in contrasts:
        sink = BytesIO(b"")
        observed[label] = refusal(document, sink, settings, expected)
        assert sink.tell() == 0 and sink.getvalue() == b""
    return observed


def prove(case, request, authority, scratch):
    source = FromData(request["document"])
    name = source.metadata["name"]
    report, old = authority
    (entry,) = (row for row in loads(report)["cases"] if row["name"] == name)
    expected = entry["candidate_sha256" if old else "artifact_sha256"]
    leaf = name + ".SLDPRT"
    path = scratch / leaf
    locator = "C:\\KitSdkCandidates\\" + leaf
    measurement = {"written_at": request["created_at"], "receipt": {"native_report": report}}
    values = {"final_destination": locator, MEASURE: measurement, "require_native_transfers": True}
    path_values = {key: value for key, value in values.items() if key != "final_destination"}
    preload()
    GetDocumentCaps(source)
    guard = OutputGuard(scratch, leaf)
    sys.addaudithook(guard.audit)
    with guard.active("memory"):
        candidate = PrepareCircle(source, BytesIO(), request["created_at"], WriteOptions(values=values), Measured=True)
        payload = candidate.BytesValue
    assert digest(payload) == expected
    cases = {}
    for full in (True, False):
        with guard.active("memory"):
            document = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=full)
            assert IsCircRead(document) and (document.brep is not None) is full
            restored = CadDocument.from_json(document.to_json(indent=None))
            assert restored == document
            (sketch,) = document.sketches
            actual_centre = sketch.entities[0].attributes["native_center_m"]
            assert actual_centre == candidate.PlanValue.CircleValue.CenterValue
            assert "solidworks_source_bytes" in document.metadata
            no_carrier = replace(document, metadata={key: value for key, value in document.metadata.items()
                                                     if key != "solidworks_source_bytes"})
            restored_input = ReadCircInput(no_carrier, name)
            assert "solidworks_source_bytes" not in restored_input.metadata
            assert PrepareCircle(restored_input, BytesIO(), request["created_at"], WriteOptions(values=values),
                                 Measured=True).BytesValue == payload
            for route, current in ((registry, document), (adapter, restored), (writer, restored)):
                destination = BytesIO()
                result = route(current, destination, values)
                assert destination.getvalue() == payload
                assert_result(result, document, payload)
            failures = check_refusals(document, values, no_carrier)
        with guard.active("path"):
            result = registry(restored, path, path_values)
            assert_result(result, document, payload)
        assert path.read_bytes() == payload
        assert tuple(scratch.iterdir()) == (path,)
        path.unlink()
        with guard.active("path"):
            refusal(document, path, {key: value for key, value in path_values.items() if key != MEASURE},
                    "offline native measurement")
        assert not tuple(scratch.iterdir())
        cases["full" if full else "design_only"] = {
            "exact_outputs": 4, "refusals": {**failures, "unmeasured_path": "offline native measurement"},
            "linked_design_body": document.bodies[0].id,
            "independent_generation_without_source_carrier": True,
            "display_centre_mm": (sketch.entities[0].geometry.center.x, sketch.entities[0].geometry.center.y),
            "typed_centre_m": actual_centre,
            "drivers": len(document.parameters),
            "selected_configuration": document.configurations[0].name,
        }
    assert not guard.denied
    return {"case": case, "archive_sha256": expected, "receipt_sha256": digest(report.encode()),
            "readback_routes": cases, "runtime_input_file_reads": len(guard.denied), "native_processes": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", choices=DISCLOSED, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    args = parser.parse_args()
    request = loads((args.requests / (args.case + ".json")).read_bytes())
    with TemporaryDirectory(prefix="KitColdCirc-") as folder:
        row = prove(args.case, request, report_inputs(args.case), Path(folder).resolve())
    print(dumps(row, sort_keys=True, allow_nan=False))
