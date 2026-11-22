from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from gzip import decompress
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from os import name as os_name
from pathlib import Path, PureWindowsPath
from subprocess import run as run_process
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveMeasuredPrincipalRevolve import ROOT, WriterAudit, digest, written
from ProveMeasuredThinRevolve import PINS, emit, reject
from ThinProofModel import WALL_MODES, neutral
from ThinPathLease import measured_target, own_root, prove_lease
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Container.Container import (
    BuildSldprt, SldprtArchive, SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import KeywordsStream
from interchange import CadDocument
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.Features.ThinRevolve import ThinRevolve

FIXTURE = ROOT / "re/solidworks/v2026/corpus/revolve/ThinMeasured01/DisclosedEvidence.json.gz"
FIXTURE_SHA = "f72de5faf4bc7f849dd0bc48443312700b06641d6cd06aa817f8249bac06edba"
CASES = {"front": "ThinUnequal", "principal": "ThinRightCenterControl"}


def measure(case_id):
    blob = FIXTURE.read_bytes()
    assert digest(blob) == FIXTURE_SHA
    envelope = loads(decompress(blob))[case_id]
    spec_sha, _, job_sha, report_sha = PINS[int(case_id == "principal")]
    assert set(envelope) == {"model", "job", "result"}
    assert all(digest(envelope[key].encode("utf-8")) == expected for key, expected in (
        ("model", spec_sha), ("job", job_sha), ("result", report_sha),
    ))
    spec, job, report = (loads(envelope[key]) for key in ("model", "job", "result"))
    name = CASES[case_id]
    (case,) = (value for value in spec["cases"] if value["name"] == name)
    (observed,) = (value for value in report["cases"] if value["case"] == name)
    assert report["passed"] and observed["passed"] and report["job_sha256"] == job_sha
    leaf = f"{name}.SLDPRT"
    expected = job["files"][f"Candidates/{leaf}"]
    assert expected == observed["candidate_sha256"]
    locator = str(PureWindowsPath(job["logical_root"]) / "Candidates" / leaf)
    return case, expected, {
        "allow_carrier": False,
        "final_destination": locator,
        "solidworks_native_measurement": {
            "written_at": 1760000000,
            "receipt": {"native_result": envelope["result"], "inspection_job": envelope["job"]},
        },
    }


def read(payload, full, strict=True):
    source = BytesIO(payload) if isinstance(payload, bytes) else payload
    return open_document(source, source_format="solidworks.sldprt", include_brep=full, strict=strict)


def verify_owner(document, authored, case, full):
    (body,), (sketch,), (selection,) = document.bodies, document.sketches, document.selections
    (step,) = (step for step in document.feature_timeline if step.id == body.final_feature_id)
    assert body.name == step.name and step.sketch_id == sketch.id and step.operation == "create"
    assert isinstance(step.definition, ThinRevolve)
    assert step.definition.WallMode == WALL_MODES[case["wall_mode"]]
    assert (
        step.definition.SweepValue.AlongParameterId, *step.definition.GetWallIds(),
    ) == step.parameter_ids
    actual_drivers = {value.name: value.value for value in document.parameters}
    assert all(value.owner_id == step.id and value.role == "driving" for value in document.parameters)
    assert set(actual_drivers) == {value.name for value in authored.parameters}
    for expected in authored.parameters:
        actual = actual_drivers[expected.name]
        assert actual.unit == expected.value.unit
        assert abs(actual.value - expected.value.value) <= 1e-13
    assert selection.path[-1].entity_id == sketch.entities[1].id
    assert sketch.entities[1].construction and not sketch.entities[0].construction
    topo = body.topology
    assert (topo.solid_count, topo.face_count, topo.edge_count, topo.vertex_count) == (1, 6, 12, 8)
    assert (document.brep is not None) is full


def ambiguous_name(payload, audit):
    archive = SldprtArchive.from_bytes(payload)
    stream = archive.require(KeywordsStream)
    original = b'Name="ThinBossRevolve" Type="Revolve-Thin"'
    changed = b'Name="WrongThinName" Type="Revolve-Thin"'
    assert stream.count(original) == 1
    malformed = BuildSldprt({**archive.streams, KeywordsStream: stream.replace(original, changed)},
                            FormatVersion=4)
    for full in (True, False):
        try:
            audit.run(lambda: read(malformed, full))
        except SldprtFormatError as error:
            assert "unverified typed history" in str(error)
            assert "keyword name differs from its resolved owner" in str(error.__cause__)
        else:
            raise AssertionError("strict thin read accepted a detached keyword name")
        fallback = audit.run(lambda: read(malformed, full, strict=False))
        assert "solidworks.typed_thin_revolve_semantics" not in fallback.metadata
        assert fallback.brep is None and len(fallback.bodies) == 1
        assert all(not isinstance(step.definition, ThinRevolve) for step in fallback.feature_timeline)
    return 4


def publish_path(author, options, payload, case, token):
    target = measured_target(options["final_destination"])
    if token is None:
        raise ValueError("thin suite path worker requires its parent lease")
    prove_lease(target.parent.parent, token)
    target.parent.mkdir()
    audit = WriterAudit(target.parent)
    for route in ("registry", "direct"):
        result = audit.run(lambda: emit(author, target, options, route))
        written(lambda: result, payload)
        assert result.path == target.resolve() and not result.dropped
        assert set(target.parent.iterdir()) == {target}
        assert target.read_bytes() == payload
        verify_owner(read(target, True), author, case, True)
        target.unlink()
    observed = audit.report()
    assert observed["output_opens"] == 2
    return observed


def run(case_id, token=None):
    case, expected, options = measure(case_id)
    author = neutral(case)
    author.assert_valid()
    GetDocumentCaps(author)
    import_module("interchange.brep.Validation.BrepValidate")
    for codec in ("utf-16-le", "utf-8"):
        lookup(codec)
    with TemporaryDirectory(prefix="KitThinSuite-") as folder:
        audit = WriterAudit(Path(folder))
        stream = BytesIO()
        first = audit.run(lambda: emit(author, stream, options, "registry"))
        payload = stream.getvalue()
        assert first.vendor_loadable and first.application_usable and digest(payload) == expected
        sink = BytesIO()
        written(lambda: audit.run(lambda: emit(author, sink, options, "direct")), payload, sink)
        for full in (True, False):
            projected = audit.run(lambda: read(payload, full))
            verify_owner(projected, author, case, full)
            restored = CadDocument.from_json(ToJson(projected, IndentSize=None))
            for route in ("direct", "registry"):
                sink = BytesIO()
                result = audit.run(lambda: emit(restored, sink, options, route))
                written(lambda: result, payload, sink)
                assert GetDocumentCaps(restored) <= result.NativeCaps and not result.dropped
        negative = ambiguous_name(payload, audit)
        width = author.parameters[1]
        changed = replace(author, parameters=(
            author.parameters[0], replace(width, value=replace(width.value, value=width.value.value * 1.01)),
            *author.parameters[2:],
        ))
        for route in ("direct", "registry"):
            reject(audit, changed, options, route, "no matching native measurement")
        runtime = audit.report()
    path_runtime = publish_path(author, options, payload, case, token) if os_name == "nt" else None
    return {
        "case": case["name"], "sha256": expected, "runtime": runtime, "stream_routes": 6,
        "file_routes": 2 if path_runtime else 0, "path_runtime": path_runtime,
        "name_contrasts": negative, "unmeasured_refusals": 2, "native_launches": 0,
    }


def dispatch(case_id, token=None):
    args = [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--case",
        case_id,
        "--worker",
    ]
    if token is not None:
        args.extend(("--lease-token", token))
    return run_process(args, timeout=45, check=False).returncode


def supervise(case_id):
    if os_name != "nt":
        return dispatch(case_id)
    _, _, options = measure(case_id)
    target = measured_target(options["final_destination"])
    with own_root(target.parent.parent) as token:
        return dispatch(case_id, token)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Verify an exact disclosed thin revolve in a fresh SDK worker"
    )
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--lease-token")
    args = parser.parse_args()
    if args.worker:
        print(dumps(run(args.case, args.lease_token), sort_keys=True))
    else:
        raise SystemExit(supervise(args.case))
