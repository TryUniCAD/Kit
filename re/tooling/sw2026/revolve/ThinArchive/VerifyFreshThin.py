from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from gzip import decompress
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from os import O_CREAT, O_EXCL, O_RDWR, O_WRONLY, fstat, name as os_name
from pathlib import Path, PureWindowsPath
from stat import FILE_ATTRIBUTE_REPARSE_POINT, S_ISDIR
from tempfile import TemporaryDirectory
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(HERE.parents[1]), str(ROOT / "src")]

from RevolveFamilyModel import thin_predictions
from ThinProofModel import WALL_MODES, neutral
from convert import extract_brep, open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry import AdapterNotFoundError
from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.Features.Revolves.ThinRevolve import ThinRevolve

FIXTURE = ROOT / "re/solidworks/v2026/corpus/revolve/ThinMeasured01/DisclosedEvidence.json.gz"
EARLIER = ROOT / "re/solidworks/measurements/2026/SdkThinRevolveMeasuredPublication01.json"
GRAMMAR = ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"
FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"
CASES = {
    "ThinOne": "front", "ThinOpposite": "front", "ThinMidplane": "front",
    "ThinUnequal": "front", "ThinTopOppositeControl": "principal", "ThinRightCenterControl": "principal",
}
PINS = {
    "front": (
        "dc2fe59f7401905e84f325468384d2f60b78b9f8408204c5b0995c6d8590154d",
        "f00ddbfe7e7a9e6ba0f63c86129946f2bf7d58811d760bb5b1812520864648ea",
        "cdada047b9f9bd7be97b62383c07bcee06a527a69152af83d932801e2a556b5c",
    ),
    "principal": (
        "72341240e566c2fe027716478fa3e07b389cf4e5451e463f3c14698afe23e694",
        "f3e4cc5b5f38ff677c13e52e996e59c92afdd35128e921360c24d17db0b76aa4",
        "f0cae9a898ea4ed54a7e181b8631da6ff17569eca430558c4c77004b36d37127",
    ),
}


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, sha):
    data = path.read_bytes()
    assert digest(data) == sha, path
    return data


def evidence(name):
    batch = CASES[name]
    texts = loads(decompress(pinned(FIXTURE, "f72de5faf4bc7f849dd0bc48443312700b06641d6cd06aa817f8249bac06edba")))[batch]
    assert set(texts) == {"model", "job", "result"}
    fields = ("model", "job", "result")
    assert tuple(digest(texts[key].encode("utf-8")) for key in fields) == PINS[batch]
    spec, job, report = (loads(texts[key]) for key in fields)
    (case,) = (row for row in spec["cases"] if row["name"] == name)
    (measured,) = (row for row in report["cases"] if row["case"] == name)
    assert spec["split"] == "discovery" and measured["passed"] and report["passed"]
    leaf = "Candidates/" + name + ".SLDPRT"
    expected = job["files"][leaf]
    assert measured["candidate_sha256"] == expected
    older = loads(pinned(EARLIER, "1a86ff7d3b473bb6d8e7dd311ee495b06557b45a1bafbd0f60d6b86439ac2b68"))
    (streams,) = (row["stream_sha256"] for row in older["records"]
                  if row["case"] == name and row["generated_sha256"] == expected)
    assert len(streams) == 10
    return case, expected, streams, {
        "allow_carrier": False,
        "require_native_transfers": True,
        "final_destination": str(PureWindowsPath(job["logical_root"]) / leaf),
        MEASURE: {"written_at": 1760000000, "receipt": {
            "native_result": texts["result"], "inspection_job": texts["job"],
        }},
    }


@contextmanager
def no_reads(*, layout=False, scratch=None, output=None):
    active = True
    counts = {"forbidden_events": 0, "reader_layout_opens": 0, "output_opens": 0}

    staging_dirs = set()

    def audit(event, args):
        if not active:
            return
        if event == "open" and layout and args[0] == str(GRAMMAR) and not args[2] & (O_WRONLY | O_RDWR):
            counts["reader_layout_opens"] += 1
            return
        if scratch and event in ("open", "os.listdir", "os.scandir"):
            entry = args[0]
            if type(entry) is str:
                path = Path(entry)
                is_stage = path.parent == scratch and path.name.startswith(".") and ".kit-" in path.name
                if event == "open" and output is not None:
                    in_stage = (path.parent.parent == scratch
                                and path.parent.name.startswith(f".{output.name}.kit-"))
                    if (path == output or path.name == output.name and in_stage) and (
                        args[2] & (O_WRONLY | O_CREAT | O_EXCL)
                    ) == O_WRONLY | O_CREAT | O_EXCL:
                        counts["output_opens"] += 1
                        return
                if is_stage and path.is_dir() and (event != "open" or not args[2] & (O_WRONLY | O_RDWR)):
                    metadata = path.stat()
                    staging_dirs.add((metadata.st_dev, metadata.st_ino))
                    return
            if type(entry) is int and event in ("os.listdir", "os.scandir"):
                metadata = fstat(entry)
                if S_ISDIR(metadata.st_mode) and (metadata.st_dev, metadata.st_ino) in staging_dirs:
                    return
        if event in ("open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn",
                     "os.startfile", "ctypes.dlopen") or event.startswith(
                         ("subprocess.", "os.exec", "os.spawn", "socket.")
                     ):
            counts["forbidden_events"] += 1
            raise RuntimeError(f"unexpected runtime input or application launch: {event}: {args[:1]}")

    sys.addaudithook(audit)
    try:
        yield counts
        assert not counts["forbidden_events"]
    finally:
        active = False


def writers():
    writer, adapter = SldprtWriter(), SldprtAdapter()

    def public(document, target, values, **options):
        return write_document(document, target, destination_format=FORMAT, values=values, allow_carrier=False, **options)

    def direct(document, target, values, **options):
        return writer.write(document, target, options=WriteOptions(values=values, **options))

    def adapter_write(document, target, values, **options):
        return adapter.write(document, target, options=WriteOptions(values=values, **options))

    return public, direct, adapter_write


def refuse(write, document, values, expected, **options):
    sink = BytesIO(b"untouched")
    try:
        write(document, sink, values, **options)
    except (ValueError, TypeError, AdapterNotFoundError) as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError("unqualified thin revolve published")
    assert sink.getvalue() == b"untouched" and sink.tell() == 0


def assert_written(result, document, target, payload):
    assert target.getvalue() == payload
    assert result.vendor_loadable and result.application_usable and not result.dropped
    assert result.path is None and result.adapter == FORMAT and result.bytes_written == len(payload)
    assert GetDocumentCaps(document) <= result.native_capabilities and not result.carrier_capabilities
    assert result.metadata[MEASURE]["generated_sha256"] == digest(payload)


def check_readback(document, author, case, full):
    document.assert_valid()
    (body,), (sketch,), (selection,) = document.bodies, document.sketches, document.selections
    (feature,) = (row for row in document.feature_timeline if row.id == body.final_feature_id)
    definition = feature.definition
    assert type(definition) is ThinRevolve and definition.WallMode == WALL_MODES[case["wall_mode"]]
    assert feature.operation == "create" and feature.name == body.name and feature.sketch_id == sketch.id
    (profile, axis) = sketch.entities
    assert axis.construction and not profile.construction and not sketch.closed_profile_entity_ids
    assert selection.path[-1].entity_id == axis.id and feature.selection_ids == (selection.id,)
    assert definition.SweepValue.AxisSelectionId == selection.id
    assert feature.parameter_ids == (definition.SweepValue.AlongParameterId, *definition.GetWallIds())
    assert len(document.parameters) == len(author.parameters)
    drivers = {row.name: row for row in document.parameters}
    for expected in author.parameters:
        current = drivers[expected.name]
        assert current.owner_id == feature.id and current.role == "driving"
        assert current.value.unit == expected.value.unit
        assert isclose(current.value.value, expected.value.value, rel_tol=1e-12)
    (configuration,) = document.configurations
    assert configuration.active and configuration.name == author.configurations[0].name
    (support,) = (row for row in document.support_planes if row.id == sketch.support_plane_id)
    assert support.transform == author.support_planes[0].transform
    assert not document.brep_payloads and (document.brep is not None) is full
    if not full:
        return {"drivers": list(drivers), "feature_count": len(document.feature_timeline)}
    topology = body.topology
    assert (topology.solid_count, topology.shell_count, topology.face_count,
            topology.edge_count, topology.vertex_count) == (1, 1, 6, 12, 8)
    assert not document.brep.validate(frozenset((body.id,)))
    prediction = next(row for sign, row in thin_predictions(dict(case, first_wall_sign=1)) if sign in (None, 1))
    assert isclose(topology.volume, prediction["volume_m3"] * 1e9, rel_tol=2e-12)
    assert isclose(topology.surface_area, prediction["area_m2"] * 1e6, rel_tol=2e-12)
    bounds = [coordinate for point in (topology.bounding_box.minimum, topology.bounding_box.maximum)
              for coordinate in (point.x, point.y, point.z)]
    assert all(isclose(x, y * 1000, rel_tol=2e-12, abs_tol=2e-11)
               for x, y in zip(bounds, prediction["bounds_m"], strict=True))
    return {"faces": topology.face_count, "edges": topology.edge_count, "vertices": topology.vertex_count,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area,
            "centroid_m_from_model": prediction["com_m"], "drivers": list(drivers)}


def rejects(write, document, values):
    envelope = values[MEASURE]
    receipt = envelope["receipt"]
    first = document.parameters[1]
    changed = replace(document, parameters=(
        document.parameters[0], replace(first, value=replace(first.value, value=first.value.value * 1.01)),
        *document.parameters[2:],
    ))
    controls = (
        (changed, values, "no matching native measurement"),
        (document, {key: value for key, value in values.items() if key != MEASURE}, "offline native measurement"),
        (document, {**values, "final_destination": values["final_destination"] + ".elsewhere"}, "exact inspected self locator"),
        (document, {**values, MEASURE: {**envelope, "written_at": envelope["written_at"] + 1}}, "exact archive creation epoch"),
        (document, {**values, MEASURE: {**envelope, "receipt": {**receipt,
             "inspection_job": receipt["inspection_job"] + " "}}}, "authenticated offline evidence"),
        (document, {**values, MEASURE: {**envelope, "receipt": {**receipt,
             "native_result": receipt["native_result"] + " "}}}, "authenticated offline evidence"),
    )
    for subject, settings, expected in controls:
        refuse(write, subject, settings, expected)
    refuse(write, document, values, "write configuration is unavailable", configuration="Missing")
    return len(controls) + 1


def check_windows_path(author, settings, routes, payload):
    assert os_name == "nt"
    destination = Path(settings["final_destination"])
    root = destination.parent.parent
    assert root.parent == Path("C:/") and destination.parent.name == "Candidates"
    root.mkdir()
    root_inode = root.lstat()
    parent = destination.parent
    try:
        parent.mkdir()
        output_opens = 0
        for write in routes:
            with no_reads(scratch=parent, output=destination) as audit:
                result = write(author, destination, settings)
            assert result.path == destination and result.vendor_loadable and result.application_usable
            assert result.metadata[MEASURE]["generated_sha256"] == digest(payload)
            assert destination.read_bytes() == payload and tuple(parent.iterdir()) == (destination,)
            destination.unlink()
            assert audit["output_opens"] == 1
            output_opens += audit["output_opens"]
        return output_opens
    finally:
        current = root.lstat()
        if ((current.st_dev, current.st_ino) != (root_inode.st_dev, root_inode.st_ino)
                or current.st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("measured path lease changed during publication")
        parent.rmdir()
        root.rmdir()


def verify(name, scratch, windows_path):
    case, expected, streams, settings = evidence(name)
    authored = neutral(case)
    author_json = CadDocument.from_json(ToJson(authored))
    assert authored == author_json
    authored.assert_valid()
    routes = writers()
    with no_reads() as generation:
        compiled = PrepareRevolve(authored, BytesIO(), 1760000000, WriteOptions(values=settings)).BytesValue
        actual = digest(compiled)
        archive = SldprtArchive.from_bytes(compiled)
        assert {path: digest(raw) for path, raw in archive.streams.items()} == streams
        publications = 0
        refusals = 0
        matching = actual == expected
        if not matching:
            assert "zlib-ng" in ZLIB_RUNTIME_VERSION, (name, actual, expected, ZLIB_RUNTIME_VERSION)
        for write in routes:
            if matching:
                for source in (authored, author_json):
                    sink = BytesIO()
                    assert_written(write(source, sink, settings, configuration=source.configurations[0].id),
                                   source, sink, compiled)
                    publications += 1
                refusals += rejects(write, authored, settings)
            else:
                refuse(write, authored, settings, "no matching native measurement")
                refusals += 1
    raw_folder = scratch / "Raw"
    raw_folder.mkdir()
    with no_reads(layout=True) as read_audit:
        inspected = {}
        inspected_docs = {}
        for full in (False, True):
            read = open_document(BytesIO(compiled), source_format=FORMAT, strict=True, include_brep=full)
            inspected_docs[full] = read
            inspected["full" if full else "design"] = check_readback(read, authored, case, full)
        try:
            extract_brep(BytesIO(compiled), raw_folder, source_format=FORMAT)
        except SldprtFormatError as error:
            assert str(error) == "SLDPRT contains no readable Parasolid payload"
        else:
            raise AssertionError("cache-free thin archive exposed raw Parasolid output")
    assert not tuple(raw_folder.iterdir())
    raw_folder.rmdir()
    with no_reads() as cold_audit:
        for write in routes:
            refuse(write, inspected_docs[False], settings, "native-only feature definitions")
            expected_scope = ("exact passing SOLIDWORKS 2026 SP05.2 oracle report"
                              if write.__name__ == "direct" else "does not support the destination")
            refuse(write, inspected_docs[True], settings, expected_scope)
    target = scratch / (name + ".SLDPRT")
    target.write_bytes(b"untouched")
    for write in routes:
        with no_reads(scratch=scratch) as rejected_path:
            try:
                write(authored, target, {**settings, "final_destination": str(target)}, overwrite=True)
            except ValueError as error:
                assert "inspected" in str(error), str(error)
            else:
                raise AssertionError("unmeasured thin revolve path published")
        assert target.read_bytes() == b"untouched" and tuple(scratch.iterdir()) == (target,)
    path_publications = check_windows_path(authored, settings, routes, compiled) if matching and windows_path else 0
    return {"case": name, "status": "exact" if matching else "unmeasured_compressor_refused",
            "generated_sha256": actual, "expected_sha256": expected, "path_publications": path_publications,
            "streams": len(streams), "publications": publications, "refusals": refusals + 3 * len(routes),
            "runtime_input_reads": generation["forbidden_events"] + cold_audit["forbidden_events"] + rejected_path["forbidden_events"],
            "read_runtime_input_reads": read_audit["forbidden_events"],
            "reader_layout_opens": read_audit["reader_layout_opens"], "readback": inspected,
            "native_result_sha256": PINS[CASES[name]][2]}


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify one disclosed thin revolve in a fresh process")
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--windows-path", action="store_true")
    args = parser.parse_args()
    if args.windows_path and os_name != "nt":
        parser.error("--windows-path requires an exclusive measured C: target")
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    with TemporaryDirectory(prefix="KitMeasuredThinPort-") as folder:
        output = verify(args.case, Path(folder).resolve(), args.windows_path)
    print(dumps({**output, "platform": sys.platform, "runtime": ZLIB_RUNTIME_VERSION,
                 "native_processes": 0, "protected_inputs": 0}, sort_keys=True, allow_nan=False))
