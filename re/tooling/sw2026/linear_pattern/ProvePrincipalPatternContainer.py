from argparse import ArgumentParser
from codecs import lookup
from collections import defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from subprocess import run
import sys
from xml.etree.ElementTree import fromstring
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProvePrincipalPatternDirection import MEASUREMENTS, PLACEMENT_PIN, ROOT, VERSION, expect, line_owner, pinned, wire
from ProvePrincipalPatternDrivers import AXES, PITCH_VIEW, ZERO, finish, inspect_drivers, replay, words
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import KPatDriveSlots, PatDriveStyle
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PrincPatInput import PrincPatInput
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import FrontStockBox
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import SeedStockInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Patterns.CheckPatMode import CheckPatMode
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.BuildColdPat import BuildColdPat
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatStocks import ReadPatStocks
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import PatternOwner
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatChain import ReadPatChain
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDatum import ReadPatDatum
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDrivers import ReadPatDrivers
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.brep.Validation.BrepValidate import GetBrepErrors

BASE = "d13afaf44c66b55399e4daf7efb9d765238c9380"
KEY_CHANGES = {KeywordsStream, KResolvedFeaturesStream}


def digest(data):
    return sha256(data).hexdigest()


def build_input(request):
    name, axis, epoch = (request[key] for key in ("name", "axis", "epoch"))
    plate, seed = (tuple(tuple(map(float, coords)) for coords in request[key]) for key in ("plate", "seed"))
    stock = SeedStockInput(
        name, "Default", f"C:\\KitPrincipalPatternCold\\{name}.SLDPRT", epoch,
        FrontStockBox("PlateSketch", "PlateBoss", plate), FrontStockBox("SeedSketch", "SeedBoss", seed),
    )
    views = {"D1": "*Front", "D3": PITCH_VIEW.get(axis)}
    labels = {"D1": tuple(request["count_label"]), "D2": seed[0], "D4": tuple(request["idle_label"])}
    if request.get("contrast") == "oblique_view":
        views["D1"] = "*Back"
    if request.get("contrast") == "shifted_pitch":
        labels["D3"] = (0.0, 0.005, 0.0)
    styles = tuple(PatDriveStyle(name, views.get(name), labels.get(name, ZERO), True, 0)
                   for _, name, _ in KPatDriveSlots)
    return PrincPatInput(
        stock, axis, request.get("reverse", axis == "y"), request.get("pattern", "LinearPattern"),
        request["count"], request["pitch"], styles,
    )


def read_owners(link, headers, request):
    features = IndexFeatures(link)
    expect(tuple(features.values()) == link.ResolvedValue.RootsValue and len(features) == 22,
           "principal pattern does not retain one complete ordered root inventory")
    plate_profile, plate, seed_profile, seed, pattern = link.ResolvedValue.RootsValue[-5:]
    plane_name = "Right Plane" if request["axis"] == "x" else "Top Plane"
    expect(tuple(ReadNativeName(node) for node in (plate_profile, plate, seed_profile, seed, pattern)) ==
           ("PlateSketch", "PlateBoss", "SeedSketch", "SeedBoss", "LinearPattern")
           and not any(node.ClassValue.NameValue == "moRefAxis_c" for node in features.values()),
           "principal tree changed a source role or added an axis")
    CheckPatMode(pattern, IsCold=True)
    atoms, final = ReadPatChain(link, (plate_profile, plate, seed_profile, seed, pattern), IsCold=True)
    datum = ReadPatDatum(link, headers[1], features, pattern)
    direction = line_owner(pattern.FieldsValue["f1288"], link.ResolvedValue.RootsValue, link.ConfigValue, headers)
    normal = datum.FrameValue.NormalValue
    signed = tuple(-value for value in normal) if datum.ReversedValue else normal
    expect(ReadNativeName(datum.PlaneValue) == plane_name and words(signed) == words(AXES[request["axis"]])
           and all(DatumTime(header, pattern.FieldsValue["f08"]) == request["epoch"]
                   and header.FieldsValue["f08"] == pattern.FieldsValue["f08"] + 1 for header in headers),
           "principal selected datum, direction or creation log differs")
    drivers = ReadPatDrivers(link, pattern)
    dim_ids = tuple(driver.DimensionValue.FieldsValue["f50"] for driver in drivers)
    expect(dim_ids == tuple(range(pattern.FieldsValue["f08"] - 6, pattern.FieldsValue["f08"])),
           "principal pattern was not allocated after its six actual dimensions")
    owner = PatternOwner(pattern, seed, datum, drivers, atoms, final)
    return owner, direction


def dimensions(link, request):
    axis, count, pitch = (request[key] for key in ("axis", "count", "pitch"))
    first = tuple(map(float, request["seed"][0]))
    index = "xy".index(axis)
    end = finish(first, pitch, axis)
    start = first[index]
    delta = end[index] - start
    midpoint = ((start + delta / 2.0) - start) / delta
    values = inspect_drivers(link, dict(request, first=first, count=count, pitch=pitch,
                                      midpoint=midpoint))
    expected = {"*Top": 200, "*Front": 201} if axis == "x" else {"*Top": 200, "*Left": 201, "*Front": 202}
    live = {"D1": ["*Front", expected["*Front"]], "D3": [PITCH_VIEW[axis], expected[PITCH_VIEW[axis]]]}
    expect(values["catalog_ids"] == expected and values["active_views"] == live
           and values["slots"]["D2"]["label"] == first and values["slots"]["D4"]["label"] == tuple(request["idle_label"]),
           "standard annotation order or six display presentation owners differ")
    return {"catalog_ids": expected, "active_views": live, "pitch_world_extent_m": values["pitch_local_extent_m"],
            "pitch_midpoint_word": values["pitch_midpoint_word"], "typed_driver_values": [
        [name, row["value"], row["display_cache"], row["display_id"], row["dimension_id"]]
        for _, name, _ in KPatDriveSlots for row in (values["slots"][name],)
    ]}


def predictions(request):
    plate, seed = [tuple(tuple(coord * 1000 for coord in point) for point in request[key]) for key in ("plate", "seed")]
    width, height, depth = plate[1]
    (x0, y0, _), (x1, y1, z1) = seed
    wide, high, rise = x1 - x0, y1 - y0, z1 - depth
    count = request["count"]
    pitch = request["pitch"] * 1000
    repeat = count * (count - 1) / 2
    volume_plate, volume_seed = width * height * depth, wide * high * rise
    volume = volume_plate + volume_seed * count
    area = 2 * (width * height + width * depth + height * depth) + count * 2 * (wide + high) * rise
    plate_center = (width / 2, height / 2, depth / 2)
    seed_center = ((x0 + x1) / 2, (y0 + y1) / 2, (z1 + depth) / 2)
    direction = AXES[request["axis"]]
    centroid = tuple((volume_plate * base + volume_seed * (count * center + repeat * sense * pitch)) / volume
                     for base, center, sense in zip(plate_center, seed_center, direction, strict=True))
    return volume, area, centroid, (0.0, 0.0, 0.0, width, height, z1)


def prove_solid(link, owner, request):
    body_id = "local-pattern-result"
    solid = BuildColdPat(link, owner, ReadPatStocks(link, owner), body_id)
    boundary, stats = solid.BrepValue, solid.TopologyValue
    (shell,) = boundary.shells
    (region,) = boundary.regions
    (body,) = boundary.bodies
    count = request["count"]
    expect(shell.closed and region.solid and body.design_body_id == body_id
           and len(shell.face_use_ids) == len(boundary.faces) == 6 + 5 * count
           and stats.face_count == len(boundary.faces) and stats.edge_count == 12 * (count + 1)
           and stats.vertex_count == 8 * (count + 1) and stats.solid_count == stats.shell_count == 1
           and not GetBrepErrors(boundary, frozenset((body_id,))),
           "reconstructed raised boundary does not retain a single closed solid")
    outer = {loop.id: loop.outer for loop in boundary.loops}
    (raised_face,) = (face for face in boundary.faces if len(face.loop_ids) > 1)
    expect(tuple(outer[key] for key in raised_face.loop_ids) == (True,) + (False,) * count,
           "single plate face does not contain one joined inner rim per raised instance")
    incidence = defaultdict(list)
    for coedge in boundary.coedges:
        incidence[coedge.edge_id].append(coedge.reversed)
    expect(set(incidence) == {edge.id for edge in boundary.edges}
           and all(sorted(uses) == [False, True] for uses in incidence.values()),
           "a joined rim or stock edge lacks exactly two opposing uses")
    volume, area, centroid, bounds = predictions(request)
    actual_bounds = stats.bounding_box
    measured_bounds = tuple(getattr(point, axis) for point in (actual_bounds.minimum, actual_bounds.maximum) for axis in "xyz")
    measured_center = solid.EvidenceValue["centroid_mm"]
    decimals = (*measured_center, *measured_bounds, stats.volume, stats.surface_area)
    expect(all(isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-10)
               for observed, expected in zip(decimals, (*centroid, *bounds, volume, area), strict=True)),
           "typed solid mass and bounds differ from independent rectangular cell integration")
    expect(solid.ProducerValue is owner.NodeValue and not solid.EvidenceValue["native_kernel_identity"],
           "solid proof needs the real pattern producer and strictly typed computed geometry")
    return {"body_count": 1, "face_count": stats.face_count, "edge_count": stats.edge_count,
            "vertex_count": stats.vertex_count, "plate_hole_loops": count,
            "volume_mm3": stats.volume, "area_mm2": stats.surface_area, "bounds_mm": measured_bounds,
            "centroid_mm": measured_center}


def prove_keywords(raw, owner, link, request):
    root = fromstring(raw[1:])
    features = IndexFeatures(link)
    rows = {int(row.attrib["id"]): row for row in root if row.tag != "Configuration"}
    pattern = rows[owner.NodeValue.FieldsValue["f08"]]
    datum = rows[owner.DatumValue.PlaneValue.FieldsValue["f08"]]
    config = root[0]
    order = tuple((row.tag, row.attrib["id"]) for row in root if row.tag != "Configuration")
    expect(raw[0] == 0x86 and b" />" not in raw and root.tag == "Keywords"
           and root.attrib == {"Name": request["name"], "id": str(request["epoch"])}
           and (config.tag, config.attrib["Name"]) == ("Configuration", "Default")
           and order == tuple(sorted(order))
           and set(rows) == set(features) and len(root) == len(rows) + 1
           and all(row.attrib["Name"] == ReadNativeName(features[key]) for key, row in rows.items()),
           "compact Keywords do not enumerate the actual linked feature inventory")
    expect((pattern.tag, pattern.attrib["Type"]) == ("Feature", "LPattern")
           and tuple(row.attrib["Name"] for row in pattern) == ("D1", "D3")
           and int(pattern[0].text) == request["count"]
           and isclose(float(pattern[1].text) / 1000.0, request["pitch"], rel_tol=1e-15)
           and (datum.tag, datum.attrib["Type"], len(datum)) == ("Feature", "Plane", 0)
           and all("°" not in (row.text or "") for row in root.iter("Dimension")),
           "principal Keyword rows acquired a phantom angular driver or wrong pattern dimension")
    return {"root_count": len(rows), "pattern_drivers": [row.attrib["Name"] for row in pattern],
            "datum_without_dimension": int(datum.attrib["id"]), "framing": "compact"}


def worker():
    from LocalPatternContainerProcess import audit, linked

    request = json.load(sys.stdin)
    for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    audit.BeginBuild()
    graph = MakePatGraph(build_input(request))
    streams, payload = EmitPatArchive(graph)
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    replayed, headers = linked(payload, streams)
    actual = replay(link, link.ConfigValue.HeaderValue, archive.require(link.ConfigName), archive.require(link.StreamName))
    expect(len(streams) == 10 and set(streams) == set(archive.streams)
           and actual["map"] == [replayed.ConfigValue.MapValue.CounterValue, replayed.ResolvedValue.MapValue.CounterValue]
           and link.ResolvedValue.ExtraFields is None
           and graph.AxisValue is graph.AngleValue is None
           and sum(node is graph.PlaneValue for node in graph.RootsValue) == 1,
           "principal composer lost a typed stream or repeated an existing system datum")
    owner, direction = read_owners(link, headers, request)
    report = {
        "payload_bytes": len(payload), "payload_sha256": digest(payload), "request_sha256": digest(wire(request)),
        "streams": {key: {"sha256": digest(raw), "bytes": len(raw)} for key, raw in streams.items()},
        "map_counters": [link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue],
        "principal_direction": direction, "atom_lineage": owner.AtomsValue,
        "final_atom_map": owner.OutputValue.IndexValue, "pattern_feature_id": owner.NodeValue.FieldsValue["f08"],
        "drivers": dimensions(link, request), "solid": prove_solid(link, owner, request),
        "keywords": prove_keywords(streams[KeywordsStream], owner, link, request), "runtime_reads": len(audit.DeniedReads),
    }
    expect(not audit.DeniedReads, "principal composer or typed geometry attempted runtime input access")
    metadata = wire(report)
    sys.stdout.buffer.write(len(metadata).to_bytes(4, "little") + metadata + payload)


def execute(request, refusal=None):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=wire(request),
                 cwd=ROOT, capture_output=True, check=False, timeout=60)
    if refusal is not None:
        expect(result.returncode != 0 and not result.stdout and refusal in result.stderr.decode(),
               "wrong principal model or guard refusal: " + result.stderr.decode())
        return result.stderr.decode().splitlines()[-1]
    expect(result.returncode == 0 and not result.stderr, result.stderr.decode())
    end = 4 + int.from_bytes(result.stdout[:4], "little")
    report = json.loads(result.stdout[4:end])
    payload = result.stdout[end:]
    expect(digest(payload) == report["payload_sha256"] and len(payload) == report["payload_bytes"],
           "isolated process returned mismatched container authority")
    return report, payload


def disclosures(packet_root):
    report = {}
    placement = json.loads(pinned(MEASUREMENTS / "LocalLinearPatternDatumPlacement01.json", PLACEMENT_PIN))["principal"]
    for name, member in placement.items():
        expect(name[:4] in ("D01X", "D02Y"), "unexpected disclosed principal file")
        raw = pinned(packet_root / "DisclosedNative" / name[:4] / name, member["sha256"])
        keywords = SldprtArchive.from_bytes(raw).require(KeywordsStream)
        root = fromstring(keywords[1:])
        (pattern,) = (row for row in root if row.attrib.get("Type") == "LPattern")
        rows = [(row.attrib["Name"], row.text) for row in pattern]
        expect(b" />" not in keywords and set(name for name, _ in rows) == {"D1", "D3"}
               and len(rows) == 2 and pattern.attrib["Name"] == "LinearPattern",
               "disclosed principal Keyword case changed physical framing or active drivers")
        report[name] = {"source_sha256": member["sha256"], "keywords_sha256": digest(keywords),
                        "active_dimensions": rows, "framing": "compact"}
    expect(len(report) == 6, "incomplete principal Keyword disclosure")
    return report


def supervise(packet_root, destination):
    synthetic = {
        "right": {"name": "PrincipalRightOrigin", "axis": "x", "epoch": 1795590161, "count": 3, "pitch": 0.031875,
                  "plate": [[0, 0, 0], [0.1695, 0.112, 0.009]], "seed": [[0.029, 0.035, 0], [0.04275, 0.0465, 0.02175]],
                  "count_label": [0.065, 0.041, 0.0], "idle_label": [0.029, 0.055, 0.0]},
        "top": {"name": "PrincipalTopOrigin", "axis": "y", "epoch": 1795590169, "count": 5, "pitch": 0.01975,
                "plate": [[0, 0, 0], [0.153, 0.1515, 0.01325]], "seed": [[0.074, 0.105, 0], [0.0845, 0.1145, 0.0295]],
                "count_label": [0.075, 0.089, 0.0], "idle_label": [0.054, 0.105, 0.0]},
    }
    reports, payloads = {}, {}
    for name, spec in synthetic.items():
        reports[name] = {}
        for phase, request in (("initial", spec), ("count", dict(spec, count=spec["count"] + 1)),
                               ("pitch", dict(spec, pitch=0.025125 if name == "right" else 0.020625))):
            report, payload = execute(request)
            reports[name][phase] = report
            payloads[phase, f'{spec["name"]}.SLDPRT'] = payload
            if phase == "initial":
                expect(execute(request) == (report, payload), "initial principal container is not deterministic")
                continue
            baseline = reports[name]["initial"]
            expect({key for key in report["streams"] if report["streams"][key] != baseline["streams"][key]} == KEY_CHANGES
                   and report["map_counters"] == baseline["map_counters"]
                   and report["atom_lineage"] == baseline["atom_lineage"]
                   and report["final_atom_map"] == baseline["final_atom_map"],
                   "independent principal edit changed unrelated streams or managed identities")
    right, top = synthetic["right"], synthetic["top"]
    refusals = {
        "unwitnessed_sign": execute(dict(right, reverse=True), "forward Right or reversed Top"),
        "front_direction": execute(dict(right, axis="z"), "forward Right or reversed Top"),
        "extra_root_name": execute(dict(right, pattern="Right Plane"), "must be distinct actual native names"),
        "overhang": execute(dict(right, pitch=0.14), "wholly interior to the plate"),
        "touching_rims": execute(dict(right, pitch=0.01375), "must remain strictly separated"),
        "oblique_anno": execute(dict(top, contrast="oblique_view"), "Front count and its signed pitch view"),
        "shifted_pitch_label": execute(dict(right, contrast="shifted_pitch"), "Front count and its signed pitch view"),
    }
    sources = disclosures(packet_root)
    if destination is not None:
        expect(not destination.resolve().is_relative_to(ROOT), "generated research files require a directory outside Kit")
        destination.mkdir()
        for (phase, name), payload in payloads.items():
            folder = destination / phase
            folder.mkdir(exist_ok=True)
            with (folder / name).open("xb") as handle:
                handle.write(payload)
    sys.stdout.buffer.write(wire({
        "schema": "kit.sw2026.principal-pattern-container.v1", "base": BASE, "native_build_authority": "34.5.2.0604",
        "source_placement_sha256": PLACEMENT_PIN, "disclosed_keywords": sources, "model_cases": reports,
        "guarded_workers": 15, "modeled_files": 6, "typed_stream_replays": 54, "complete_streams": 60,
        "compressor": ZLIB_RUNTIME_VERSION, "refusals": refusals, "runtime_reads": 0, "new_native_processes": 0,
        "protected_inputs_read": 0, "public_writer_qualified": False, "tool_sha256": digest(HERE.read_bytes()),
    }))


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--worker", action="store_true")
    modes.add_argument("--packet-root", type=Path)
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
    else:
        supervise(args.packet_root, args.artifacts)


if __name__ == "__main__":
    main()
