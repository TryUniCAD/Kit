from argparse import ArgumentParser
from codecs import lookup
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from PatternPlaneDirectionRule import resolve_local_plane
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.PatternTailFields import KPatternTailFields
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import PutHingeViews
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.MakePatDir import MakePatDir
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import ReadPatDir
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatFeature import MakePatFeature
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import FrontStockBox
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakePatternSeed import MakePatternSeed
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedHeaders import MakeSeedHeaders
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import SeedStockInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

VERSION = 19000
BASE = "e0d4349f18711d5ba9a04171c8a4b84d6e6603db"
PLACEMENT_PIN = "827baa41493ed7fc459dcb5d7b4485a733494cf20fd4fb8d9ecb5aee4a70f566"
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
RULES = tuple(rule for rule in KPatternTailFields if (rule.KindValue, rule.NameValue)
              in (("Mask", "pattern_datum"), ("Validate", "OrdinaryPatternDatum")))


def expect(value, message):
    if not value:
        raise ValueError(message)


def wire(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def pinned(path, digest):
    data = path.read_bytes()
    expect(sha256(data).hexdigest() == digest, f"known disclosure changed: {path.name}")
    return data


def vector(fields):
    return tuple(fields[key] for key in "xyz")


def line_bits(fields):
    return pack("<8dB", *vector(fields["fc8"]), *vector(fields["fe0"]), fields["fb0"], fields["fb8"], fields["f68"])


def line_owner(line, roots, config, headers):
    fields = line.FieldsValue
    reference = fields["f58"].FieldsValue
    datum_id = reference["ff0"]["f00"]
    (plane,) = (node for node in roots if node.ClassValue.NameValue == "moRefPlane_c" and node.FieldsValue["f08"] == datum_id)
    component = reference["f58"]
    line_value = ReadPatDir(plane)
    expect(component.FieldsValue["owner"] is config.RootValue
           and component is not config.RootValue.FieldsValue["f990"]
           and fields["f60"] is None and fields["f0c"] == 0
           and all(DatumTime(header, datum_id) == reference["ff0"]["f08"] for header in headers)
           and reference["ff8"] is None and reference["f100"] == line_value.RoleValue
           and line_bits(fields) == pack("<8dB", *line_value.PointValue, *line_value.DirectionValue, 0.0, line_value.SpanValue, 1),
           "pattern direction lost its actual allocated plane, header or ordered coordinates")
    return {"plane_id": datum_id, "plane_role": line_value.RoleValue, "creation_epoch": reference["ff0"]["f08"],
            "display_centre_m": list(line_value.PointValue), "normal": list(line_value.DirectionValue), "span": line_value.SpanValue}


def source_probe(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    headers = (link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require("Header2"), VERSION))
    (feature,) = (root for root in link.ResolvedValue.RootsValue if root.ClassValue.NameValue == "moLPattern_c")
    line = feature.FieldsValue["f1288"]
    evidence = line_owner(line, link.ResolvedValue.RootsValue, link.ConfigValue, headers)
    cfg, inherited = WriteConfigMut(link.ConfigValue.RootValue, VERSION, headers[0])
    resolved, written = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                    VERSION, inherited.MapValue, link.ResolvedValue.ContextValue)
    expect(cfg == archive.require(link.ConfigName) and resolved == archive.require(link.StreamName)
           and written.MapValue == link.ResolvedValue.MapValue, "disclosed principal pattern ceased to replay exactly")
    return evidence | {"archive_sha256": sha256(raw).hexdigest(), "reversed": feature.FieldsValue["f1298"],
                       "frames": [sha256(value).hexdigest() for value in (cfg, resolved)]}


def encode_field(pattern, seed, link_context):
    expect(len(RULES) == 2, "expected the existing scoped f1288 field and validation")
    context = MakeResolvedCtx(VERSION, seed, link_context, None)
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), context, WriteBodyMut)
    frame = WriteFrame(writer, FieldScope(pattern.FieldsValue), pattern, WriteSchemaMut, WriteFieldsMut)
    WriteFieldsMut(frame, RULES)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def read_field(data, pattern, seed, link_context):
    context = MakeResolvedCtx(VERSION, seed, link_context, None)
    cursor = BinaryReader(data)
    reader = GraphReader(cursor, ArchiveMaps(seed.CounterValue, seed), partial(ReadBodyMut, context))
    frame = ReadFrame(context, reader, FieldScope(pattern.FieldsValue), pattern, ReadSchemaMut, ReadFieldsMut)
    ReadFieldsMut(frame, RULES)
    expect(not cursor.GetRemaining(), "generated direction member has trailing bytes")
    return reader.MapValue.Snapshot()


def expected_line(request):
    width, height, depth = request["plate"]
    depth = max(depth, request["seed"][1][2])
    half_width, half_height, half_depth = (value * 0.5 for value in (width, height, depth))
    width_border, height_border, depth_border = (value * 0.5 + value * 0.05 for value in (width, height, depth))
    if request["axis"] == "x":
        return resolve_local_plane((0.0, half_height, half_depth), (-0.0, -0.0, -1.0), (1.0, 0.0, 0.0),
                                   (depth_border, -depth_border, height_border, -height_border))
    return resolve_local_plane((half_width, 0.0, half_depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                               (width_border, -width_border, depth_border, -depth_border))


def model_probe(request):
    name = request["name"]
    stock = MakePatternSeed(SeedStockInput(name, "Default", "C:\\KitPrincipalPattern\\" + name + ".SLDPRT", request["epoch"],
                            FrontStockBox("StockSketch", "StockBoss", ((0.0, 0.0, 0.0), tuple(request["plate"]))),
                            FrontStockBox("RaisedSketch", "RaisedBoss", tuple(map(tuple, request["seed"])))))
    system, allocator = stock.SystemValue, stock.Allocator
    plane = system.SystemValues.PlaneValues[request["axis"]]
    if request.get("mode") != "empty_display":
        PutHingeViews(system, stock.BoundsValue)
    role = request.get("mode")
    headers = MakeSeedHeaders(stock, *((plane,) if request["allocated_epoch"] else ()))
    if role == "detached_plane":
        plane = ArchiveNode(plane.ClassValue, dict(plane.FieldsValue))
    if role == "crossed_headers":
        headers = (headers[0], MakeSeedHeaders(stock)[1], headers[2])
    if role == "missing_peer_event":
        headers[1].FieldsValue["f20"] = MakeSeedHeaders(stock)[1].FieldsValue["f20"]
    if role == "off_plane_display":
        plane.FieldsValue["f6f8"].FieldsValue["display_root"][request["axis"]] = 0.125
    line = MakePatDir(system, stock.SettingsValue, allocator, plane, headers[:2])
    pattern = MakePatFeature(stock, "LinearPattern")
    pattern.FieldsValue["f1288"] = line
    config, graph = WriteConfigMut(system.RootValue, VERSION, headers[0])
    manager = ReadCmgrMut(WriteCmgrMut(system.ManagerValue, VERSION), VERSION)
    link_context = MakeLinkContext(graph, manager)
    header_reads = tuple(ReadHeaderGraph(WriteHeadGraph(header, VERSION), VERSION) for header in headers[:2])
    config_read = ReadConfigMut(config, VERSION, header_reads[0])
    body, previous = WriteResolMut(stock.RootsValue, None, VERSION, graph.MapValue, link_context)
    earlier = ReadResolvedMut(body, VERSION, config_read.MapValue, link_context)
    field, written = encode_field(pattern, previous.MapValue, link_context)
    decoded = ArchiveNode(pattern.ClassValue, {})
    loaded = read_field(field, decoded, earlier.MapValue, link_context)
    repeated, _ = encode_field(decoded, earlier.MapValue, link_context)
    expect(field == repeated and written.CounterValue == loaded.CounterValue
           and tuple((row.IndexValue, getattr(row.EntryValue, "ClassValue", row.EntryValue)) for row in written.EntriesValue)
           == tuple((row.IndexValue, getattr(row.EntryValue, "ClassValue", row.EntryValue)) for row in loaded.EntriesValue),
           "selected principal pattern wire or class and object slots differ")
    snapshot = line_owner(decoded.FieldsValue["f1288"], earlier.RootsValue, config_read, header_reads)
    expected = expected_line(request)
    expect(line_bits(decoded.FieldsValue["f1288"].FieldsValue)
           == pack("<8dB", *expected["fc8"], *expected["fe0"], expected["fb0"], expected["fb8"], expected["f68"])
           and snapshot["creation_epoch"] == (request["epoch"] if request["allocated_epoch"] else 2592000)
           and snapshot["plane_role"] == {"x": 1, "y": 2}[request["axis"]],
           "neutral model direction differs from its independent envelope or creation")
    return snapshot | {"body_graph_sha256": sha256(body).hexdigest(), "field_bytes": len(field),
                       "field_sha256": sha256(field).hexdigest(), "map": [previous.MapValue.CounterValue, loaded.CounterValue]}


def worker(mode):
    raw = sys.stdin.buffer.read()
    for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    evidence = source_probe(raw) if mode == "source" else model_probe(json.loads(raw))
    expect(not audit.DeniedReads, "unexpected external input from pattern direction")
    sys.stdout.buffer.write(wire(evidence | {"runtime_file_reads": 0}))


def launch(mode, data, refusal=None):
    result = run((sys.executable, "-I", "-B", __file__, "--worker", mode), cwd=ROOT, input=data,
                 capture_output=True, check=False, timeout=60)
    if refusal:
        expect(result.returncode and not result.stdout and refusal in result.stderr.decode(), "wrong principal direction refusal")
        return result.stderr.decode().splitlines()[-1]
    expect(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return json.loads(result.stdout)


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--capture", type=Path)
    modes.add_argument("--worker", choices=("source", "model"))
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    sources = json.loads(pinned(MEASUREMENTS / "LocalLinearPatternDatumPlacement01.json", PLACEMENT_PIN))["principal"]
    disclosed = {}
    for name, row in sources.items():
        expect(name[:4] in ("D01X", "D02Y"), "unexpected principal disclosure")
        evidence = launch("source", pinned(args.capture / name[:4] / name, row["sha256"]))
        placement = row["placement"]
        horizontal, _, normal = placement["basis_u_v_n"]
        exact = resolve_local_plane(placement["display_origin_m"], horizontal, normal, placement["ordered_borders_m"])
        expect(evidence["display_centre_m"] == list(exact["fc8"]) and evidence["normal"] == list(exact["fe0"])
               and evidence["span"] == exact["fb8"] and evidence["plane_id"] == placement["plane_id"]
               and evidence["reversed"] == int(name.startswith("D02Y")), "independent principal source expectation differs")
        disclosed[name] = evidence
    neutral = {
        "right": {"name": "PrincipalRight", "axis": "x", "epoch": 1795590001, "plate": [0.151, 0.101, 0.012],
                  "seed": [[0.011, 0.048, 0.0], [0.023, 0.058, 0.027]], "allocated_epoch": False},
        "top": {"name": "PrincipalTop", "axis": "y", "epoch": 1795590003, "plate": [0.188, 0.092, 0.0175],
                "seed": [[0.056, 0.014, 0.0], [0.077, 0.021, 0.036]], "allocated_epoch": True},
    }
    generated = {}
    for name, request in neutral.items():
        evidence = launch("model", wire(request))
        expect(evidence == launch("model", wire(request)), "independent guarded principal model workers disagree")
        generated[name] = evidence
    negatives = {
        "front": launch("model", wire(neutral["right"] | {"axis": "z"}), "requires an ordinary Top or Right datum"),
        "empty_display": launch("model", wire(neutral["right"] | {"mode": "empty_display"}), "requires two finite positive spans"),
        "detached_plane": launch("model", wire(neutral["right"] | {"mode": "detached_plane"}), "actual registered principal plane"),
        "crossed_headers": launch("model", wire(neutral["top"] | {"mode": "crossed_headers"}), "requires paired local part headers"),
        "missing_peer_event": launch("model", wire(neutral["top"] | {"mode": "missing_peer_event"}), "creation differs between its own headers"),
        "off_plane_display": launch("model", wire(neutral["right"] | {"mode": "off_plane_display"}), "requires an ordinary Top or Right datum"),
    }
    sys.stdout.buffer.write(wire({"schema": "kit.sw2026.principal-pattern-selected-direction.v1", "base": BASE,
                                 "source_geometry_receipt_sha256": PLACEMENT_PIN, "native_build": "34.5.2.0604",
                                 "source": disclosed, "generated_model": generated, "refusals": negatives,
                                 "guarded_workers": 16, "new_native_launches": 0, "heldout_inputs_read": 0,
                                 "writer_files_published": 0, "tool_sha256": sha256(HERE.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
