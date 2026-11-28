from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from io import BytesIO
from importlib import import_module
from json import dumps, loads
from math import cos, isclose, radians, sin
from pathlib import Path, PureWindowsPath
from subprocess import check_output
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveMeasuredPrincipalRevolve import (
    WriterAudit, digest, source_fingerprint, written,
)
from ThinProofModel import WALL_MODES, neutral, world
from convert import extract_brep, open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.Features.ThinRevolve import ThinRevolve

PINS = (
    (
        "dc2fe59f7401905e84f325468384d2f60b78b9f8408204c5b0995c6d8590154d",
        "33a91b5797f3e5c8374f962ff9803e7770b248b8e0150633f7ddd5e42e9285f0",
        "f00ddbfe7e7a9e6ba0f63c86129946f2bf7d58811d760bb5b1812520864648ea",
        "cdada047b9f9bd7be97b62383c07bcee06a527a69152af83d932801e2a556b5c",
    ),
    (
        "72341240e566c2fe027716478fa3e07b389cf4e5451e463f3c14698afe23e694",
        "21228b9c95c2135a826bbbdb7d1c0abd37ff94de08d34fc6f59c934d64fe9a6a",
        "f3e4cc5b5f38ff677c13e52e996e59c92afdd35128e921360c24d17db0b76aa4",
        "f0cae9a898ea4ed54a7e181b8631da6ff17569eca430558c4c77004b36d37127",
    ),
)


def pinned(path, sha):
    raw = path.read_bytes()
    assert digest(raw) == sha, path
    return raw.decode("utf-8")


def load_case(args, index):
    batch = int(index >= 4)
    work = (args.front / "Packet", args.principal / "Packet")[batch]
    spec_sha, build_sha, job_sha, native_sha = PINS[batch]
    spec = loads(pinned(work / "ModelSpec.json", spec_sha))
    build = loads(pinned(work / "BuildReceipt.json", build_sha))
    job_text = pinned(work / "NativeJob.json", job_sha)
    native_text = pinned((args.front / "NativeResult.json", args.principal_result)[batch], native_sha)
    job, result = loads(job_text), loads(native_text)
    assert result["job_sha256"] == job_sha and result["build_receipt_sha256"] == build_sha
    case = spec["cases"][index - 4 * batch]
    name = case["name"]
    leaf = f"{name}.SLDPRT"
    reference_name = f"References/{name}.reopen.json"
    reference = loads(pinned(work / reference_name, job["files"][reference_name]))["reopened"]
    expected = job["files"][f"Candidates/{leaf}"]
    native = next(value for value in result["cases"] if value["case"] == name)
    assert native["passed"] and native["candidate_sha256"] == expected
    return case, reference, expected, build["rows"][name], {
        "allow_carrier": False,
        "final_destination": str(PureWindowsPath(job["logical_root"]) / "Candidates" / leaf),
        "solidworks_native_measurement": {
            "written_at": build.get("epoch", build.get("common_epoch")),
            "receipt": {"native_result": native_text, "inspection_job": job_text},
        },
    }


def check_shape(document, case, reference, full):
    (body,), (sketch,), (selection,) = document.bodies, document.sketches, document.selections
    (step,) = (step for step in document.feature_timeline if step.id == body.final_feature_id)
    definition = step.definition
    assert isinstance(definition, ThinRevolve) and definition.WallMode == WALL_MODES[case["wall_mode"]]
    assert step.name == body.name and step.operation == "create"
    assert len(sketch.entities) == 2 and not sketch.constraints and not sketch.closed_profile_entity_ids
    assert selection.path[-1].entity_id == sketch.entities[1].id
    assert sketch.entities[1].construction and not sketch.entities[0].construction
    assert step.sketch_id == sketch.id and len(step.input_feature_ids) == 1
    assert len(document.parameters) == len(reference["drivers"])
    assert (definition.SweepValue.AlongParameterId, *definition.GetWallIds()) == step.parameter_ids
    expected = {item["name"].split("@")[0]: item["value"] for item in reference["drivers"].values()}
    for parameter in document.parameters:
        scalar = parameter.value.value
        if parameter.value.unit == "mm":
            scalar *= 0.001
        assert parameter.owner_id == step.id and parameter.role == "driving"
        assert isclose(scalar, expected[parameter.name], rel_tol=1e-14)
    topology = body.topology
    measured = reference["measured"]
    assert (topology.solid_count, topology.shell_count) == (1, 1)
    assert (topology.face_count, topology.edge_count, topology.vertex_count) == (
        measured["faces"], measured["edges"], measured["vertices"],
    )
    assert isclose(topology.volume * 1e-9, measured["volume_m3"], rel_tol=2e-12)
    assert isclose(topology.surface_area * 1e-6, measured["area_m2"], rel_tol=2e-12)
    bounds = [value * 0.001 for point in (topology.bounding_box.minimum, topology.bounding_box.maximum)
              for value in (point.x, point.y, point.z)]
    assert all(isclose(x, y, rel_tol=2e-12, abs_tol=2e-14)
               for x, y in zip(bounds, measured["bounds_m"], strict=True))
    assert (document.brep is not None) is full and not document.brep_payloads
    if full:
        assert not document.brep.validate(frozenset((body.id,)))
    center = sector_centroid(case, definition.WallMode)
    assert all(isclose(x, y, rel_tol=2e-12, abs_tol=2e-14)
               for x, y in zip(center, measured["com_m"], strict=True))
    return {"volume_mm3": topology.volume, "area_mm2": topology.surface_area,
            "centroid_m_from_neutral": center, "dimensions": sorted(expected)}


def sector_centroid(case, mode):
    radius = case["profile_radius_m"]
    first, second = case["wall_m"]
    inner, outer = {
        "one_sided": (radius, radius + first),
        "opposite": (radius - first, radius),
        "midplane": (radius - first * 0.5, radius + first * 0.5),
        "two_sided": (radius - second, radius + first),
    }[mode]
    factor = 2 * (outer**3 - inner**3) / (3 * (outer**2 - inner**2))
    theta = radians(case["angle_deg"])
    return world(case, (
        case["axis_x_m"] + factor * sin(theta) / theta,
        sum(case["axial_m"]) / 2,
        -factor * (1 - cos(theta)) / theta,
    ))


def emit(document, sink, settings, route):
    if route == "direct":
        return SldprtWriter().write(document, sink, options=WriteOptions(values=settings))
    return write_document(document, sink, destination_format="solidworks.sldprt", values=settings)


def reject(audit, document, settings, route, expected):
    sink = BytesIO()
    try:
        audit.run(lambda: emit(document, sink, settings, route))
    except ValueError as error:
        assert expected in str(error), (expected, type(error).__name__, str(error))
        assert sink.getvalue() == b""
    else:
        raise AssertionError("unmeasured document was published")


def run_worker(args):
    case, reference, expected, build, settings = load_case(args, args.worker)
    document = neutral(case)
    document.assert_valid()
    GetDocumentCaps(document)
    import_module("interchange.brep.Validation.BrepValidate")
    for codec in ("utf-16-le", "utf-8"):
        lookup(codec)
    with TemporaryDirectory(prefix="KitMeasuredThinRevolve-") as directory:
        audit = WriterAudit(Path(directory))
        sink = BytesIO()
        initial = audit.run(lambda: emit(document, sink, settings, "direct"))
        payload = sink.getvalue()
        assert initial.vendor_loadable and initial.application_usable and digest(payload) == expected
        streams = SldprtArchive.from_bytes(payload).streams
        hashes = {name: digest(data) for name, data in streams.items()}
        lengths = {name: len(data) for name, data in streams.items()}
        assert len(streams) == 10 and streams.keys() == build["typed_streams"].keys()
        assert all(hashes[name] == item["sha256"] and lengths[name] == item["bytes"]
                   for name, item in build["typed_streams"].items())
        sink = BytesIO()
        written(lambda: audit.run(lambda: emit(document, sink, settings, "registry")), payload, sink)
        positives = ["authored_direct", "authored_registry"]
        for full in (True, False):
            got = audit.run(lambda: open_document(
                BytesIO(payload), source_format="solidworks.sldprt", strict=True, include_brep=full,
            ))
            observed = check_shape(got, case, reference, full)
            restored = CadDocument.from_json(ToJson(got, IndentSize=None))
            for route in ("direct", "registry"):
                sink = BytesIO()
                result = audit.run(lambda: emit(restored, sink, settings, route))
                written(lambda: result, payload, sink)
                assert GetDocumentCaps(restored) <= result.NativeCaps
                positives.append(("geometry" if full else "design") + "_json_" + route)
        old = document.parameters[1]
        modified = replace(document, parameters=(
            document.parameters[0], replace(old, value=replace(old.value, value=old.value.value * 1.01)),
            *document.parameters[2:],
        ))
        mismatched = {**settings, "final_destination": settings["final_destination"] + ".wrong"}
        envelope = settings["solidworks_native_measurement"]
        dishonest = {**settings, "solidworks_native_measurement": {**envelope, "receipt": {
            **envelope["receipt"], "native_result": envelope["receipt"]["native_result"] + "\n",
        }}}
        stale = {**settings, "solidworks_native_measurement": {
            **envelope, "written_at": envelope["written_at"] + 1,
        }}
        refusals = (
            (modified, settings, "no matching native measurement"),
            (document, mismatched, "exact inspected self locator"),
            (document, dishonest, "authenticated offline evidence"),
            (document, stale, "exact archive creation epoch"),
            (replace(restored, metadata={**restored.metadata, "extra_native_owner": 77}),
             settings, "differs from its regenerated part"),
        )
        for route in ("direct", "registry"):
            for changed, values, message in refusals:
                reject(audit, changed, values, route, message)
        try:
            audit.run(lambda: extract_brep(payload, Path(directory) / "raw", source_format="solidworks.sldprt"))
        except ValueError as error:
            assert "SLDPRT contains no readable Parasolid payload" in str(error), str(error)
        else:
            raise AssertionError("cache-free part supplied a raw payload")
        corrupt = dict(streams)
        corrupt["Contents/Config-0"] = corrupt["Contents/Config-0"][:-1]
        malformed = BuildSldprt(corrupt, FormatVersion=4)
        for full in (True, False):
            try:
                audit.run(lambda: open_document(
                    BytesIO(malformed), source_format="solidworks.sldprt", strict=True, include_brep=full,
                ))
            except ValueError as error:
                assert "unverified typed history" in str(error), str(error)
            else:
                raise AssertionError("truncated typed history passed strict read")
        return {"case": case["name"], "generated_sha256": expected, "bytes": len(payload),
                "positive_paths": positives, "refusals": 2 * len(refusals),
                "strict_history_refusals": 2, "raw_payload_refusals": 1,
                "stream_sha256": hashes, "stream_lengths": lengths,
                "geometry": observed, "runtime": audit.report()}


def main():
    parser = ArgumentParser()
    parser.add_argument("--front", type=Path, required=True)
    parser.add_argument("--principal", type=Path, required=True)
    parser.add_argument("--principal-result", type=Path, required=True)
    parser.add_argument("--worker", type=int, choices=range(6))
    args = parser.parse_args()
    if args.worker is not None:
        print(dumps(run_worker(args)))
        return
    records = [loads(check_output(
        [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:], "--worker", str(i)],
    )) for i in range(6)]
    print(dumps({
        "schema": "kit.sw2026.measured-thin-revolve-public.v1", "fresh_workers": len(records),
        "new_native_processes": 0, "new_heldout_credit": 0, "protected_inputs": 0,
        "native_authorities": [pins[-1] for pins in PINS], "records": records,
        "platform": sys.platform,
        "source_fingerprint": source_fingerprint(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "neutral_model_script_sha256": digest(Path(__file__).with_name("ThinProofModel.py").read_bytes()),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
