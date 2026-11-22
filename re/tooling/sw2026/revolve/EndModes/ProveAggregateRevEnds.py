from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
FIXTURE = ROOT / "re/solidworks/v2026/corpus/revolve/MeasuredEnd01"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"),
                str(HERE.parent), str(HERE.parent.parent / "PrincipalReader")]

from AuditPrincipalReader import make_guard
from ProveTwoDirectionRevolves import warm
from VerifySdkCircleEndRegistration import OutputGuard, refuses
from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve

MEASURE = "solidworks_native_measurement"
FORMAT = "solidworks.sldprt"
CASES = ("EndSingle", "EndMidplane", "EndTwo", "EndTwoReverse")
EVIDENCE = {"generation_receipt": "Generation.json", "native_result": "Result.json", "inspection_job": "Job.json"}


def digest(data):
    return sha256(data).hexdigest()


def projection(raw, authored, native, full):
    result = open_document(BytesIO(raw), source_format=FORMAT, strict=True, include_brep=full)
    document = CadDocument.from_json(result.to_json())
    feature, = (row for row in document.feature_timeline if type(row.definition) is AngularRevolve)
    sketch, = document.sketches
    selection, = document.selections
    body, = document.bodies
    stored = {parameter.id: parameter for parameter in document.parameters}
    drivers = tuple(stored[key] for key in feature.parameter_ids)
    definition = feature.definition
    original = authored.feature_timeline[0].definition
    assert definition.SideMode == original.SideMode and definition.AxisDirection == original.AxisDirection
    assert definition.AlongParameterId == drivers[0].id
    assert definition.AgainstParameterId == (drivers[1].id if len(drivers) == 2 else None)
    assert len(drivers) == len(authored.parameters)
    assert all(d.owner_id == feature.id and d.role == e.role and (d.name, d.value) == (e.name, e.value)
               for d, e in zip(drivers, authored.parameters, strict=True))
    assert feature.sketch_id == sketch.id and selection.id == definition.AxisSelectionId
    axis, = (row for row in sketch.entities if row.construction)
    assert tuple(row.entity_id for row in selection.path) == (sketch.id, axis.id)
    assert len(sketch.constraints) == 4 and body.final_feature_id == feature.id
    assert (document.brep is not None) == full and not document.brep_payloads
    counts = body.topology
    assert counts.solid_count == 1
    if full:
        assert (counts.shell_count, counts.face_count, counts.edge_count, counts.vertex_count) == (1, 6, 12, 8)
        assert isclose(counts.volume, native["volume"] * 1e9, rel_tol=5e-7)
        assert isclose(counts.surface_area, native["area"] * 1e6, rel_tol=5e-7)
    else:
        assert counts.face_count == 0 and counts.volume is None and counts.surface_area is None
    return [driver.name for driver in drivers]


def receipt_texts():
    return {role: (FIXTURE / file).read_bytes().decode("utf-8") for role, file in EVIDENCE.items()}


def negative_models(document, values, end_exact):
    locator = values["final_destination"]
    measurement = values[MEASURE]
    evidence = measurement["receipt"]
    primary, *others = document.parameters
    edited = replace(primary, value=replace(primary.value, value=primary.value.value + 0.005))
    yield document, {"final_destination": locator, "allow_non_native": True}, "offline native measurement receipt"
    yield document, {**values, "final_destination": r"C:\Foreign\Wrong.SLDPRT"}, "exact inspected self locator"
    yield document, {**values, MEASURE: {**measurement, "written_at": measurement["written_at"] + 1}}, "no matching native measurement"
    yield replace(document, parameters=(edited, *others)), values, "no matching native measurement"
    for key in evidence:
        change = {**measurement, "receipt": {**evidence, key: evidence[key] + "\n"}}
        yield document, {**values, MEASURE: change}, "authenticated offline evidence"
    yield document, values, "standalone" if end_exact else "no matching native measurement"


def verify(name, folder, disclosed):
    warm()
    evidence = receipt_texts()
    request = json.loads((FIXTURE / (name + "Request.json")).read_bytes())
    expected = json.loads(evidence["generation_receipt"])["cases"][name]
    job = json.loads(evidence["inspection_job"])["files"][name]
    report = json.loads(evidence["native_result"])
    native, = (row for row in report["cases"] if row["name"] == name)
    assert job["candidate_sha256"] == native["candidate_sha256"] == expected["archive_sha256"]
    assert job["candidate"] == request["locator"] and native["passed"] and native["native_phase_failures"] == [None, None]
    document = CadDocument.from_json(json.dumps(request["doc"]))
    proof_values = {"final_destination": request["locator"], "require_native_transfers": True,
                    MEASURE: {"written_at": request["epoch"], "receipt": evidence}}
    options = WriteOptions(values=proof_values)
    GetDocumentCaps(document)
    writer = SldprtWriter()
    filename = name + ".SLDPRT"
    guard = OutputGuard(folder, filename)
    sys.addaudithook(guard.audit)
    read_state, read_audit = make_guard(ROOT / "src")
    cad_imports = []

    def forbid_cad(event, args):
        if ((guard.mode is not None or read_state["enabled"]) and event == "import"
                and args[0].split(".")[0] in ("pythoncom", "win32com", "FreeCAD", "adsk")):
            cad_imports.append(args[0])
            raise RuntimeError("CAD dependency in the measured revolve process")

    sys.addaudithook(forbid_cad)
    with guard.active("memory"):
        candidate = PrepareRevolve(document, BytesIO(), request["epoch"], options).BytesValue
        assert PrepareRevolve(document, BytesIO(), request["epoch"], options).BytesValue == candidate
    measured_sha = expected["archive_sha256"]
    exact = digest(candidate) == measured_sha
    hashes = {key: digest(raw) for key, raw in SldprtArchive.from_bytes(candidate).streams.items()}
    assert len(hashes) == 10 and hashes == {key: row["sha256"] for key, row in expected["streams"].items()}
    if disclosed is not None:
        reference = (disclosed / filename).read_bytes()
        assert digest(reference) == measured_sha and candidate == reference

    def registry(model, target, values, **kwargs):
        return write_document(model, target, destination_format=FORMAT, values=values, allow_carrier=False, **kwargs)

    def direct(model, target, values, **kwargs):
        return writer.write(model, target, WriteOptions(values=values, **kwargs))

    routes = (registry, direct)
    published = 0
    rejected = 0
    file = folder / "sink.sldprt"
    original_evidence = {**evidence, "native_result": evidence["native_result"].replace("\n", "\r\n")}
    original_values = {**proof_values, MEASURE: {**proof_values[MEASURE], "receipt": original_evidence}}
    with file.open("x+b") as sink:
        for route, target in ((registry, BytesIO()), (direct, BytesIO()), (registry, sink)):
            values = original_values if route is direct else proof_values
            with guard.active("memory"):
                if exact:
                    result = route(document, target, values)
                    assert result.vendor_loadable and result.application_usable
                    assert not result.dropped and not result.carrier_capabilities
                    assert result.native_capabilities == GetDocumentCaps(document)
                    assert result.bytes_written == len(candidate)
                    assert result.metadata[MEASURE]["generated_sha256"] == measured_sha
                    assert result.metadata[MEASURE]["native_result_sha256"] == digest(original_evidence["native_result"].encode())
                    assert result.metadata[MEASURE]["edit_record_sha256"] == native["native_phase_sha256"][0]
                    assert result.metadata[MEASURE]["reopen_record_sha256"] == native["native_phase_sha256"][1]
                    if isinstance(target, BytesIO):
                        assert target.getvalue() == candidate
                    published += 1
                else:
                    assert "no matching native measurement" in refuses(
                        lambda: route(document, target, values), (ValueError,))
                    assert target.tell() == 0
                    rejected += 1
    assert file.read_bytes() == (candidate if exact else b"")
    seen = []
    with guard.active("memory"):
        for model, values, wanted in negative_models(document, proof_values, exact):
            for route in routes:
                sink = BytesIO(b"caller owned")
                sink.seek(3)
                error = refuses(lambda: route(model, sink, values), (ValueError, TypeError))
                assert wanted in error, (wanted, error)
                assert sink.getvalue() == b"caller owned" and sink.tell() == 3
                seen.append(wanted)
                rejected += 1
    native_geometry = native["comparisons"]["reopened"]["actual"]
    read_state["enabled"] = True
    try:
        full = projection(candidate, document, native_geometry, True)
        assert read_audit["grammar_reads"] == 0
        design = projection(candidate, document, native_geometry, False)
        assert full == design
    finally:
        read_state["enabled"] = False

    path = folder / filename
    for route in routes:
        with guard.active("path"):
            error = refuses(lambda: route(document, path, proof_values), (ValueError,))
        assert "filesystem destination differs" in error and not path.exists()
        assert not any(entry.name.startswith("." + filename + ".kit-") for entry in folder.iterdir())
        rejected += 1
    sentinel = b"existing owned file"
    path.write_bytes(sentinel)
    for route in routes:
        with guard.active("path"):
            error = refuses(lambda: route(document, path, proof_values, overwrite=True), (ValueError,))
        assert "filesystem destination differs" in error and path.read_bytes() == sentinel
        assert {entry.name for entry in folder.iterdir()} == {file.name, path.name}
        rejected += 1
    assert not guard.denied and not cad_imports and not read_audit["unexpected_attempts"]
    return {"name": name, "runtime": ZLIB_RUNTIME_VERSION, "streams": hashes,
            "candidate_sha256": digest(candidate), "measured_sha256": measured_sha,
            "native_measurement_exact": exact, "bytes": len(candidate), "drivers": full,
            "publications": published, "refusals": rejected, "native_processes": 0,
            "runtime_input_reads": 0, "strict_reader_packaged_layout_reads": read_audit["grammar_reads"],
            "whole_archive_independently_compared": disclosed is not None}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--disclosed", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitAggregateRevEnd-") as output:
        print(json.dumps(verify(args.case, Path(output).resolve(), args.disclosed), sort_keys=True))
