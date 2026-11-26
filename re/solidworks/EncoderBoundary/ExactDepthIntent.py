from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import subprocess
import sys


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return sha256(raw).hexdigest()


def measurement(root, name):
    return json.loads((root / "re/solidworks/measurements/2026" / name).read_bytes())


def pinned_case(root, label):
    if label == "WarmedNoOpAfter":
        index = measurement(root, "VendorBossCorpus/SourceContrasts.json")
        run = index["runs"]["Discovery02"]
        if run["healthy_controls"] is not True:
            raise ValueError("the warmed authoring controls did not pass")
        return "NoOpAfter", run["cases"]["NoOpAfter"]["archive_sha256"], run["lifetimes"]["Author"]["record_sha256"]
    if label not in ("BaselineSource", "BaselineEditedControl"):
        raise ValueError("exact depth bridge requires a disclosed calibration case")
    body = measurement(root, "VendorBlindBossBodyOwnership.json")
    row = body["cases"][label]
    if row["directed_boundary_match"] is not True or row["api_comparisons_passed"] != 11:
        raise ValueError("the recorded calibration body proof is incomplete")
    return label, row["source_sha256"], row["source_record_sha256"]


def ordered_api_vertices(observed):
    segments = observed["sketch_segments"]
    if observed["sketch_relations"] != 0 or not 3 <= len(segments) <= 64:
        raise ValueError("the independently authored sketch is outside the plain line loop")
    starts, ends = [], []
    for segment in segments:
        start, end = segment["points"]
        if segment["kind"] != 0 or len(start) != 3 or len(end) != 3 or start[2] != 0 or end[2] != 0:
            raise ValueError("the independently authored sketch is not a planar line loop")
        starts.append(start)
        ends.append(end)
    if ends != starts[1:] + starts[:1]:
        raise ValueError("the independently authored lines are not a directed closed loop")
    return [[x * 1000, y * 1000] for x, y, _ in starts]


def read_witness(args):
    sys.path.insert(0, str(args.root / "re/solidworks/EncoderBoundary"))
    from InspectVendorBodyOwners import REVISION, cases, compare_oracle, inspect, verify_dependency

    verify_dependency(args.dependency_root)
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import ReadBodyOwner
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Features.FeatureExtrude import ExtrudeFeature

    name, expected, record_digest = pinned_case(args.root, args.case)
    selected, = (row for row in cases(args.source_record) if row[0] == name)
    _, source_path, archive_hash, author_hash, observed = selected
    if (archive_hash, author_hash) != (expected, record_digest):
        raise ValueError("authoring record differs from its pinned provenance")
    raw = source_path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("native source differs from its pinned provenance")
    inferred = inspect(raw)
    comparisons = compare_oracle(observed, inferred)
    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    driver, = document.parameters
    sketch, = document.sketches
    config, = document.configurations
    body, = document.bodies
    feature, = (value for value in document.feature_timeline if value.id == body.final_feature_id)
    archive = SldprtArchive.from_bytes(raw, "<disclosed exact depth source>")
    link = ReadNativeLink(archive, 0)
    owner = ReadExtrude(link, ReadBodyOwner(link, None), IndexFeatures(link))
    depth = owner.RequireDepth()
    native = depth.Parameter.FieldsValue["f58"]
    if (
        document.source.sha256 != expected or document.units != "mm"
        or config.active is not True or config.id != "sldprt:configuration:0"
        or owner.ModeValue != "blind" or owner.IsReversed or owner.SecondValue is not None
        or feature.id != f"sldprt:feature:{NativeNodeId(owner.NodeValue)}"
        or sketch.id != f"sldprt:sketch:{NativeNodeId(owner.ProfileValue)}"
        or feature.sketch_id != sketch.id or driver.owner_id != feature.id
        or feature.parameter_ids != (driver.id,) or driver.name != "D1" or driver.role != "driving"
        or driver.expression is not None or driver.value.unit != "mm"
        or type(feature.definition) is not ExtrudeFeature or feature.definition.length != driver.value
        or depth.DepthValue.name != "D1" or depth.DepthValue.native_role != "driving"
        or type(native) is not float or any(
            type(value) is not float or value.hex() != native.hex()
            for value in (depth.DepthValue.native_value, driver.attributes.get("native_value"), observed["depth_m"])
        )
    ):
        raise ValueError("source does not bind the proven native D1 to its linked blind boss")
    if digest(source_path.read_bytes()) != expected or digest(args.source_record.read_bytes()) != record_digest:
        raise ValueError("source provenance changed during exact depth inspection")
    return {
        "case": args.case, "source_archive_sha256": expected, "author_record_sha256": record_digest,
        "reader_revision": REVISION, "native_driver_m_binary64": native.hex(),
        "driver_owner": "moLengthParameter_c.f58",
        "source_feature_id": feature.id, "source_sketch_id": sketch.id,
        "directed_body_comparisons": comparisons, "partition_sha256": inferred["partition_sha256"],
        "source_volume_mm3": inferred["volume_mm3"], "faces_edges_vertices": inferred["faces_edges_vertices"],
        "authored_profile_mm": ordered_api_vertices(observed),
        "scope": "Independent native depth evidence for an authored geometry request",
    }


def setup(root):
    sys.path[:0] = [str(root / "src"), str(root / "re/automation"), str(root / "re")]


def directed_match(observed, expected):
    return len(observed) == len(expected) and any(
        observed == expected[index:] + expected[:index] for index in range(len(expected))
    )


def ordered_geometry(sketch):
    order, = sketch.closed_profile_entity_ids
    entities = {entity.id: entity.geometry for entity in sketch.entities}
    return tuple(entities[part] for part in order)


def prepare(args):
    setup(args.root)
    from EncoderRoundTrip.Source import decode_writer_input, encode_writer_input
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from interchange.document.Models.DocumentModel import CadDocument

    geometry = args.geometry.read_bytes()
    neutral = CadDocument.from_json(geometry.decode("utf-8"))
    encode_writer_input(neutral)
    PlanPartWrite(neutral)
    inherited = subprocess.check_output([
        sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--root", str(args.root), "witness",
        "--dependency-root", str(args.dependency_root.resolve()),
        "--source-record", str(args.source_record.resolve()), "--case", args.case,
    ])
    evidence = json.loads(inherited)
    native = float.fromhex(evidence["native_driver_m_binary64"])
    driver, = neutral.parameters
    feature, = neutral.feature_timeline
    length = replace(driver.value, value=native, unit="m")
    prepared = replace(
        neutral,
        parameters=(replace(driver, value=length),),
        feature_timeline=(replace(feature, definition=replace(feature.definition, length=length)),),
    )
    plan = PlanPartWrite(prepared)
    profile = tuple((line.start.x, line.start.y) for line in ordered_geometry(neutral.sketches[0]))
    expected = tuple(tuple(point) for point in evidence.pop("authored_profile_mm"))
    if plan.DepthValue.hex() != native.hex() or not directed_match(profile, expected):
        raise ValueError("prepared geometry does not match the independently authored directed profile and exact depth")
    if args.geometry.read_bytes() != geometry:
        raise ValueError("authored geometry input changed during depth preparation")
    payload = encode_writer_input(prepared)
    if decode_writer_input(payload, neutral.source.format_id, neutral.source.sha256) != prepared:
        raise ValueError("prepared request changed during typed JSON round trip")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "Request.json").write_bytes(payload)
    evidence.update({"authored_geometry_sha256": digest(geometry), "request_sha256": digest(payload)})
    (args.output / "SourceEvidence.json").write_bytes(canonical(evidence))
    return evidence


def guarded_candidate(document, locator, epoch):
    from EncoderRoundTrip.Solidworks import generate_prepared_candidate

    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    active, denied = True, []

    def audit(event, _):
        if active and (
            event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.spawn",
                      "os.posix_spawn", "os.startfile", "os.fork", "os.forkpty")
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            denied.append(event)
            raise RuntimeError("exact depth generation attempted external access: " + event)

    sys.addaudithook(audit)
    try:
        candidate = generate_prepared_candidate(document, native_locator=locator, written_at=epoch)
    finally:
        active = False
    if denied or any(name.startswith(("pythoncom", "win32com")) for name in sys.modules):
        raise ValueError("exact depth generation crossed its offline boundary")
    return candidate


def replay(args):
    setup(args.root)
    from EncoderRoundTrip.Source import decode_writer_input, encode_writer_input
    from convert import open_document
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import ReadColdSketch
    from interchange.document.Models.DocumentModel import CadDocument

    raw = args.request.read_bytes()
    source = CadDocument.from_json(raw.decode("utf-8")).source
    document = decode_writer_input(raw, source.format_id, source.sha256)
    driver, = document.parameters
    if driver.value.unit != "m" or document.units != "mm" or type(driver.value.value) is not float:
        raise ValueError("exact depth replay requires typed metres within a millimetre document")
    plan = PlanPartWrite(document)
    payload = guarded_candidate(document, args.native_locator, args.written_at)
    if args.request.read_bytes() != raw or encode_writer_input(document) != raw:
        raise ValueError("offline generation changed the prepared request")
    archive = SldprtArchive.from_bytes(payload, "<generated exact depth candidate>")
    if any(name.startswith("Kit/") or name.endswith("-Partition") for name in archive.streams):
        raise ValueError("generated exact depth candidate contains a carrier or retained partition")
    decoded = open_document(payload, source_format="solidworks.sldprt", strict=True)
    saved, = decoded.parameters
    shape, = decoded.bodies
    sketch, = decoded.sketches
    boss, = (value for value in decoded.feature_timeline if value.id == saved.owner_id)
    authored = ordered_geometry(document.sketches[0])
    plane, = document.support_planes
    expected, volume, _, bounds = BuildPrism(shape.id, plane.transform, authored, 0.0, plan.DepthValue / 0.001)
    actual_native = saved.attributes.get("native_value")
    topology = (len(expected.faces), len(expected.edges), len(expected.vertices))
    actual = decoded.brep
    if actual is None:
        raise ValueError("strict SDK replay did not produce an analytic boundary")
    actual_rings = ReadMassRings(actual)
    expected_rings = ReadMassRings(expected)
    matched = [tuple(i for i, ring in enumerate(expected_rings) if directed_match(value, ring)) for value in actual_rings]
    if (
        type(actual_native) is not float or actual_native.hex() != driver.value.value.hex()
        or actual_native.hex() != plan.DepthValue.hex()
        or saved.role != "driving" or saved.name != "D1" or boss.parameter_ids != (saved.id,)
        or boss.definition.length != saved.value or boss.sketch_id != sketch.id
        or shape.final_feature_id != boss.id
        or (len(actual.faces), len(actual.edges), len(actual.vertices)) != topology
        or not directed_match(ordered_geometry(ReadColdSketch(sketch)), authored)
        or shape.topology.solid_count != 1
        or any(len(row) != 1 for row in matched) or len(set(matched)) != len(expected_rings)
        or not isclose(shape.topology.volume, volume, rel_tol=0.0, abs_tol=1e-7)
        or shape.topology.bounding_box != bounds
    ):
        raise ValueError("strict SDK replay lost exact SI driving depth or the authored body")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / PureWindowsPath(args.native_locator).name).write_bytes(payload)
    report = {
        "request_sha256": digest(raw), "candidate_sha256": digest(payload), "candidate_bytes": len(payload),
        "native_locator": args.native_locator, "written_at": args.written_at,
        "readback_driver_m_binary64": actual_native.hex(),
        "volume_mm3": shape.topology.volume, "analytic_volume_mm3": volume,
        "directed_brep_rings": len(actual_rings),
        "faces_edges_vertices": topology, "external_generation_attempts": 0, "native_launches": 0,
    }
    (args.output / "CandidateEvidence.json").write_bytes(canonical(report))
    return report


if __name__ == "__main__":
    parser = ArgumentParser(description="Preserve the exact saved SOLIDWORKS blind depth in an authored research request")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    commands = parser.add_subparsers(dest="mode", required=True)
    witness = commands.add_parser("witness")
    preparation = commands.add_parser("prepare")
    for command in (witness, preparation):
        command.add_argument("--dependency-root", required=True, type=Path)
        command.add_argument("--source-record", required=True, type=Path)
        command.add_argument("--case", required=True)
    preparation.add_argument("--geometry", required=True, type=Path)
    preparation.add_argument("--output", required=True, type=Path)
    replay_parser = commands.add_parser("replay")
    replay_parser.add_argument("--request", required=True, type=Path)
    replay_parser.add_argument("--native-locator", required=True)
    replay_parser.add_argument("--written-at", required=True, type=int)
    replay_parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.root = args.root.resolve()
    handlers = {"witness": read_witness, "prepare": prepare, "replay": replay}
    sys.stdout.buffer.write(canonical(handlers[args.mode](args)))