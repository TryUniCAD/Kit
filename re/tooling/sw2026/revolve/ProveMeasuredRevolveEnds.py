from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from ProveMeasuredPrincipalRevolve import WriterAudit, denied, stream_hashes, written
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve

FIXTURE = ROOT / "re/solidworks/v2026/corpus/revolve/MeasuredEnd01"
FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
CASES = {
    "EndSingle": ("one_sided", False, 1),
    "EndMidplane": ("symmetric_full", False, 1),
    "EndTwo": ("two_sided", False, 2),
    "EndTwoReverse": ("two_sided", True, 2),
}


def digest(raw):
    return sha256(raw).hexdigest()


def inspect_document(document, expected, name):
    side, reverse, driver_count = CASES[name]
    feature, = (item for item in document.feature_timeline if type(item.definition) is AngularRevolve)
    definition = feature.definition
    drivers = [next(item for item in document.parameters if item.id == key) for key in feature.parameter_ids]
    shape, = document.bodies
    topology = shape.topology
    assert len(drivers) == driver_count and [item.name for item in drivers] == (["D1", "D2"][:driver_count])
    assert all(item.value.unit == "rad" for item in drivers)
    assert definition.SideMode == side and feature.attributes["native_reverse_direction"] is reverse
    assert len(document.selections) == 1 and len(document.sketches[0].constraints) == 4
    assert shape.final_feature_id == feature.id
    assert (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) == (1, 6, 12, 8)
    assert isclose(topology.volume, expected["volume"] * 1e9, rel_tol=5e-7)
    assert isclose(topology.surface_area, expected["area"] * 1e6, rel_tol=5e-7)
    return {item.name: item.value.value for item in drivers}


def verify(name, scratch, disclosed):
    documents = {"generation_receipt": "Generation.json", "native_result": "Result.json", "inspection_job": "Job.json"}
    evidence = {key: (FIXTURE / filename).read_bytes().decode("utf-8") for key, filename in documents.items()}
    request = loads((FIXTURE / (name + "Request.json")).read_bytes())
    expected_generation = loads(evidence["generation_receipt"])["cases"][name]
    source = loads(evidence["inspection_job"])["files"][name]
    native = loads(evidence["native_result"])
    observation, = (row for row in native["cases"] if row["name"] == name)
    assert observation["passed"] and observation["candidate_sha256"] == source["candidate_sha256"]
    assert source["candidate"] == request["locator"]
    assert source["candidate_sha256"] == expected_generation["archive_sha256"]
    reference = None if disclosed is None else (disclosed / "Assets" / (name + ".SLDPRT")).read_bytes()
    if reference is not None:
        assert digest(reference) == source["candidate_sha256"]
    document = CadDocument.from_json(dumps(request["doc"]))
    values = {"final_destination": request["locator"], OPTION: {"written_at": request["epoch"], "receipt": evidence}}
    direct = SldprtWriter()
    import_module("interchange.brep.Validation.BrepValidate")
    GetDocumentCaps(document)
    lookup("utf-16-le")
    audit = WriterAudit(scratch)

    def write(model, sink, options, registry):
        if registry:
            return write_document(model, sink, destination_format=FORMAT, values=options, allow_carrier=False)
        return direct.write(model, sink, WriteOptions(values=options))

    first = BytesIO()
    report = audit.run(lambda: write(document, first, values, True))
    candidate = first.getvalue()
    assert report.vendor_loadable and report.application_usable
    assert digest(candidate) == source["candidate_sha256"]
    if reference is not None:
        assert candidate == reference
    streams = stream_hashes(candidate)
    assert streams == {key: row["sha256"] for key, row in expected_generation["streams"].items()}
    methods = ["authored registry"]
    sink = BytesIO()
    written(lambda: audit.run(lambda: write(document, sink, values, False)), candidate, sink)
    methods.append("authored direct")
    file_path = scratch / (name + ".SLDPRT")
    with file_path.open("xb") as file_sink:
        written(lambda: audit.run(lambda: write(document, file_sink, values, True)), candidate)
    assert file_path.read_bytes() == candidate
    methods.append("authored file sink")
    expected = observation["comparisons"]["reopened"]["actual"]
    models = {}
    driver_sets = {}
    counter = 0
    for label, geometry in (("full", True), ("design", False)):
        parsed = audit.run(lambda: open_document(BytesIO(candidate), source_format=FORMAT, strict=True, include_brep=geometry))
        assert (parsed.brep is not None) == geometry
        model = CadDocument.from_json(parsed.to_json())
        driver_sets[label] = inspect_document(model, expected, name)
        models[label] = model
        for use_registry in True, False:
            sink = BytesIO()
            written(lambda: audit.run(lambda: write(model, sink, values, use_registry)), candidate, sink)
            methods.append(f"strict {label} JSON {'registry' if use_registry else 'direct'}")
            counter += 1
    assert driver_sets["full"] == driver_sets["design"]
    first_driver, *others = document.parameters
    changed_driver = replace(first_driver, value=replace(first_driver.value, value=first_driver.value.value + 0.005))
    changed_document = replace(document, parameters=(changed_driver, *others))
    changed_design = replace(models["design"], metadata={**models["design"].metadata, "extra_owner": True})
    envelope = values[OPTION]
    contrasts = [
        (document, {"final_destination": request["locator"]}, "offline native"),
        (document, {**values, "final_destination": r"C:\Foreign\Part.SLDPRT"}, "exact inspected self locator"),
        (document, {**values, OPTION: {**envelope, "written_at": request["epoch"] + 1}}, "no matching native measurement"),
        (changed_document, values, "no matching native measurement"),
        (changed_design, values, "differs from its regenerated part"),
    ]
    for key in evidence:
        modified = {**values, OPTION: {**envelope, "receipt": {**evidence, key: evidence[key] + "\n"}}}
        contrasts.append((document, modified, "authenticated offline evidence"))
    for model, options, error in contrasts:
        for use_registry in True, False:
            sink = BytesIO()
            denied(lambda: audit.run(lambda: write(model, sink, options, use_registry)), error)
            assert sink.tell() == 0 and sink.getvalue() == b""
    return {
        "case": name, "sha256": digest(candidate), "bytes": len(candidate), "streams": streams,
        "strict_json_republications": counter, "publication_routes": methods, "refusals": len(contrasts) * 2,
        "drivers_radians": driver_sets["full"], "audit": audit.report(),
        "disclosed_file_independently_compared": reference is not None, "new_native_launches": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", required=True, choices=tuple(CASES))
    parser.add_argument("--disclosed", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitMeasuredRevolveEnd-") as directory:
        print(dumps(verify(args.case, Path(directory).resolve(), args.disclosed), sort_keys=True))
