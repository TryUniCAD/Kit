from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, load, loads
from pathlib import Path, PureWindowsPath
from platform import python_version
from subprocess import run
from tempfile import TemporaryDirectory
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent), str(HERE.parents[1])]

from ColdEllipseModel import make_document
from EllipseMeasuredReceipt import normalize
from ProveCircleEndPort import OutputGuard, preload
from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Ellipse.ReadEllipAxes import ReadEllipAxes
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipRead import IsEllipRead
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import ComposeEllipse, PrepareEllipse
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadEllipInput import ReadEllipInput
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument


FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"
AUTHORITY = "e590ced10e6286c0637ea9b1bf9b8f44d041ef1b9aab454d61af0d99ec2066e3"
BASE = "0cd00727bac5068f3a21df07d6e3981b6cef3f69"
SOURCE = "09f7bca40a5332a477e0b1b5911131d6bb122ce1"


def digest(data):
    return sha256(data).hexdigest()


def registry(document, target, values):
    return write_document(document, target, destination_format=FORMAT, allow_carrier=False, values=values, overwrite=True)


def adapter(document, target, values):
    return SldprtAdapter().write(document, target, WriteOptions(values=values, overwrite=True))


def writer(document, target, values):
    return SldprtWriter().write(document, target, WriteOptions(values=values, overwrite=True))


def reject(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), (message, str(error))
    else:
        raise AssertionError("an unqualified ellipse escaped publication")


def assert_result(result, target, payload, *, source=None):
    assert result.vendor_loadable and result.application_usable
    assert not result.carrier_capabilities and not result.dropped
    assert result.bytes_written == target.tell() == len(payload)
    assert target.getvalue() == payload
    assert result.metadata[MEASURE]["generated_sha256"] == digest(payload)
    if source is not None:
        assert result.native_capabilities == GetDocumentCaps(source)
        assert result.metadata[MEASURE]["authority_sha256"] == AUTHORITY


def edit_depth(document):
    (driver,) = document.parameters
    attr = {**driver.attributes, "native_value": driver.attributes["native_value"] + 0.001}
    depth = replace(driver.value, value=attr["native_value"] / 0.001)
    step_id = document.bodies[0].final_feature_id
    timeline = tuple(replace(row, definition=replace(row.definition, length=depth))
                     if row.id == step_id else row for row in document.feature_timeline)
    return replace(document, parameters=(replace(driver, value=depth, attributes=attr),), feature_timeline=timeline)


def bad_conic(document):
    (sketch,) = document.sketches
    (entity,) = sketch.entities
    geometry = entity.geometry
    shifted = replace(geometry, center=replace(geometry.center, x=geometry.center.x + 0.25))
    return replace(document, sketches=(replace(sketch, entities=(replace(entity, geometry=shifted),)),))


def check_rejections(document, values, naked):
    stale_source = replace(document, source=replace(document.source, sha256="0" * 64))
    extra = replace(document, metadata={**document.metadata, "unrepresented": "foreign owner"})
    measurement = deepcopy(values[MEASURE])
    measurement["receipt"]["native_result_sha256"] = "b" * 64
    wrapped = "cold readback differs"
    contrasts = (
        ("altered_conic", bad_conic(document), values, "conic differs", (writer,)),
        ("edited_d1", edit_depth(document), values, wrapped, (writer,)),
        ("source_digest", stale_source, values, wrapped, (registry, adapter, writer)),
        ("unrepresented_metadata", extra, values, wrapped, (registry, adapter, writer)),
        ("absent_source_carrier", naked, values, wrapped, (registry,)),
        ("untrusted_receipt", document, {**values, MEASURE: measurement},
         "authenticated offline evidence", (registry, adapter, writer)),
        ("absent_receipt", document, {key: value for key, value in values.items() if key != MEASURE},
         "offline native measurement receipt", (registry, adapter, writer)),
        ("unmeasured_locator", document, {**values, "final_destination": values["final_destination"].replace("Candidates", "Other")},
         wrapped, (registry, adapter, writer)),
    )
    tested = {}
    for label, model, options, diagnostic, routes in contrasts:
        tested[label] = []
        for route in routes:
            target = BytesIO()
            reject(lambda: route(model, target, options), diagnostic)
            assert target.getvalue() == b"" and target.tell() == 0
            tested[label].append(route.__name__)
    for route in (registry, adapter, writer):
        target = BytesIO(b"existing native buffer")
        target.seek(3)
        reject(lambda: route(document, target, values), "empty seekable binary stream")
        assert target.getvalue() == b"existing native buffer" and target.tell() == 3
    tested["nonempty_stream"] = ["registry", "adapter", "writer"]
    return tested


def check_path(document, path, values, guard):
    sentinel = b"existing native file"
    path.write_bytes(sentinel)
    without_path = {key: value for key, value in values.items() if key != "final_destination"}
    for route in (registry, adapter, writer):
        with guard.active("path"):
            reject(lambda: route(document, path, without_path), "cold readback differs")
        assert path.read_bytes() == sentinel and tuple(path.parent.iterdir()) == (path,)
    with guard.active("path"):
        reject(lambda: writer(document, path, values), "actual final filesystem locator")
    assert path.read_bytes() == sentinel and tuple(path.parent.iterdir()) == (path,)
    path.unlink()
    return 4


def prove_modes(payload, candidate, request, values, path, guard):
    modes = {}
    for full in (True, False):
        with guard.active("memory"):
            document = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=full)
            assert IsEllipRead(document) and (document.brep is not None) is full
            assert len(document.feature_timeline) == 19
            (parameter,) = document.parameters
            (body,) = document.bodies
            assert parameter.owner_id == body.final_feature_id and parameter.name == "D1"
            (sketch,) = document.sketches
            (entity,) = sketch.entities
            (center, major, minor) = entity.attributes["native_ellipse_stations_m"]
            assert (center, major, minor) == (candidate.PlanValue.CenterValue, candidate.PlanValue.MajorValue,
                                             candidate.PlanValue.MinorValue)
            plain = ReadEllipAxes(entity.geometry, candidate.PlanValue.DepthValue)
            assert plain[:2] == (center, major) and plain[2] != minor
            restored = CadDocument.from_json(document.to_json(indent=None))
            assert restored == document
            assert "solidworks_source_bytes" in document.metadata
            naked = replace(document, metadata={key: value for key, value in document.metadata.items()
                                                if key != "solidworks_source_bytes"})
            neutral, plan = ReadEllipInput(naked, candidate.PlanValue.NameValue)
            assert plan == candidate.PlanValue
            assert "solidworks_source_bytes" not in neutral.metadata
            assert ComposeEllipse(neutral, plan, BytesIO(), request["epoch"], WriteOptions(values=values)).BytesValue == payload
            for route in (registry, adapter, writer):
                for current in (document, restored):
                    sink = BytesIO()
                    result = route(current, sink, values)
                    assert_result(result, sink, payload, source=document)
            rejected = check_rejections(document, values, naked)
        modes["full" if full else "design_only"] = {
            "exact_publications": 6,
            "exact_generation_without_raw_carrier": True,
            "verified_conic_stations_m": (center, major, minor),
            "naive_minor_m": plain[2],
            "refusals": rejected,
            "wrong_filesystem_locator_refusals": check_path(document, path, values, guard),
        }
    return modes


def worker(request, row, authority, scratch):
    source = make_document(request["model"])
    preload()
    GetDocumentCaps(source)
    clock = request["epoch"]
    locator = request["locator"]
    path = scratch / PureWindowsPath(locator).name
    guard = OutputGuard(scratch, path.name)
    sys.addaudithook(guard.audit)
    values = {"final_destination": locator, "require_native_transfers": True,
              MEASURE: {"written_at": clock, "receipt": authority}}
    with guard.active("memory"):
        candidate = PrepareEllipse(source, BytesIO(), clock, WriteOptions(values=values))
        payload = candidate.BytesValue
        assert digest(payload) == row["archive_sha256"] and len(payload) == row["archive_bytes"]
        for route in (registry, adapter, writer):
            target = BytesIO()
            result = route(source, target, values)
            assert_result(result, target, payload)
    modes = prove_modes(payload, candidate, request, values, path, guard)
    assert not guard.denied
    return {"archive_sha256": digest(payload), "native_locator": locator, "epoch": clock,
            "cases": modes, "fresh_publications": 3, "runtime_input_file_reads": len(guard.denied)}


def supervise(disclosed, output):
    authority, requests = normalize(disclosed)
    measurements = ROOT / "re/solidworks/measurements/2026"
    canonical = (dumps(authority, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    assert digest(canonical) == AUTHORITY
    assert (measurements / "SdkColdEllipseReceipt01.json").read_bytes() == canonical
    rows = {}
    for row, request in zip(authority["cases"], requests, strict=True):
        envelope = {"row": row, "request": request, "authority": authority}
        process = run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=dumps(envelope),
                      capture_output=True, text=True, timeout=180, check=False)
        assert process.returncode == 0 and not process.stderr, process.stderr
        rows[request["model"]["name"]] = loads(process.stdout)
    assert len(rows) == 2
    proof = {"schema": "kit.sw2026.cold-ellipse-republication.v1", "base_commit": BASE,
             "base_sdk_tree": SOURCE, "python": python_version(), "disclosed_authority_sha256": AUTHORITY,
             "disclosed_native_result_sha256": authority["native_result_sha256"], "fresh_processes": 2,
             "protected_inputs_read": False, "new_native_runs": 0, "cases": rows}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(dumps(proof, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker", action="store_true")
    group.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        with TemporaryDirectory(prefix="KitColdEllip-") as folder:
            print(dumps(worker(**load(sys.stdin), scratch=Path(folder).resolve()), sort_keys=True, allow_nan=False))
    else:
        if args.output is None:
            parser.error("--disclosed requires --output")
        supervise(args.disclosed, args.output)
