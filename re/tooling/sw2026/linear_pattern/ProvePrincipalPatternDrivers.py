from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import dist
from pathlib import Path
from struct import pack
from subprocess import run
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProvePrincipalPatternDirection import (
    MEASUREMENTS, PLACEMENT_PIN, ROOT, VERSION, expect, line_owner, pinned, vector, wire,
)
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import PutHingeViews
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.MakePatDir import MakePatDir
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import KPatDriveSlots, PatDriveStyle
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PutPrincMut import PutPrincMut
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.FinishPatMut import FinishPatMut
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatBoxes import MakePatBoxes
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatFeature import MakePatFeature
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import FrontStockBox
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakePatternSeed import MakePatternSeed
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedHeaders import MakeSeedHeaders
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import SeedStockInput
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import PutAnnoCatalog
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDrivers import ReadPatDrivers
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

BASE = "3171f5ac8ab0786de30d027665ee5bf184f6b412"
PACKET_PIN = "913426870bc64edb320e6a1508521c81da677a2ef4feef80b715c7859856c1bc"
SOURCE_LOCK = "8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426"
SOURCE_SPEC = "12ec4c846dda8384657480503218fd25540847fe8ff9b9c1860c92355e9de983"
SOURCE_TOOLS = {
    "Tools/LinearPatternAuthor.py": "8d09ae0316b5d04ea8e6c2f47b0f838312a484ce647fcc7ceee6ffa5ede07d37",
    "Tools/LinearPatternSpecs.py": "89e64e2acca920084bf4211ba0e3e59969b6152c4279751aafe7ae4e3379c6b5",
}
ZERO = (0.0, 0.0, 0.0)
Z = (0.0, 0.0, 1.0)
AXES = {"x": (1.0, 0.0, 0.0), "y": (-0.0, -1.0, -0.0)}
PITCH_VIEW = {"x": "*Top", "y": "*Left"}
BASIS = {"*Front": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), Z),
         "*Top": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
         "*Left": (Z, (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))}


def digest(data):
    return sha256(data).hexdigest()


def words(values):
    return pack("<" + "d" * len(values), *values)


def finish(first, pitch, axis):
    x, y, z = first
    return (x + pitch, y, z) if axis == "x" else (x, y - pitch, z)


def placement(first, second, axis):
    index = "xy".index(axis)
    start, end = first[index], second[index]
    return ((end + start) * 0.5 - start) / (end - start)


def inverse(first, axis):
    x, y, _ = first
    if axis == "x":
        return (1.0, -0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, -x, 0.0, y)
    return (-0.0, 0.0, -1.0, -1.0, -0.0, 0.0, -0.0, 1.0, 0.0, y, 0.0, x)


def linked_seed(link, pattern, first):
    (row,) = RequireNative(pattern.FieldsValue["f988"], "suObList").FieldsValue["items"]
    seed = RequireNative(row["o"], "moICE_c")
    (profile,) = ReadParents(seed)
    roots = link.ResolvedValue.RootsValue
    expect(seed in roots and profile in roots, "pattern seed does not name its actual linked earlier profile")
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    points = tuple((row["point"]["pos"]["x"], row["point"]["pos"]["y"])
                   for row in sketch.FieldsValue["points"] if row["kind"] == 0)
    expect(len(set(points)) == 4 and points[0] == first[:2]
           and tuple(map(min, zip(*points, strict=True))) == first[:2],
           "D3 anchor differs from the actual lower corner of the linked rectangular seed")
    return seed, profile


def inspect_drivers(link, request):
    pattern = RequireNative(link.ResolvedValue.RootsValue[-1], "moLPattern_c")
    model = link.ConfigValue.RootValue
    fields = model.FieldsValue
    count, pitch, *idle = ReadPatDrivers(link, pattern)
    axis = request["axis"]
    first = tuple(request["first"])
    second = finish(first, request["pitch"], axis)
    seed, sketch = linked_seed(link, pattern, first)
    live = (count, pitch)
    names = ("*Front", PITCH_VIEW[axis])
    catalog = [row["o"] for row in fields["fa48"].FieldsValue["items"]]
    registrations = {view.FieldsValue["f358"]: view for view in catalog}
    config_map = {row.IndexValue: row.EntryValue for row in link.ConfigValue.MapValue.EntriesValue}
    for driver, name in zip(live, names, strict=True):
        (member,) = driver.DisplayValue.FieldsValue["f2b0"]
        view = registrations[name]
        camera = [row["o"] for row in fields["f9f8"] if row["o"].FieldsValue["f358"] == name]
        matrix, origin = ReadRigidXform(view.FieldsValue["f368"])
        expect(type(member["v"]) is int and driver.DisplayValue.FieldsValue["n2b0"] == 1
               and matrix == tuple(BASIS[name][col][row] for row in range(3) for col in range(3))
               and origin == ZERO and view.ClassValue.NameValue == "moAnnotationView_c"
               and config_map[view.IndexValue] is view and member["v"] == view.FieldsValue["f360"]
               and len(camera) == 1 and camera[0].FieldsValue["f360"] != member["v"],
               "live display does not join the actual annotation separately from its camera")
    expect(tuple(fields["fec0"][0].values()) == (199,) and fields["feb4"] == 199 and fields["fd44"] == 12
           and fields["feb0"] == max(view.FieldsValue["f360"] for view in catalog),
           "view registry or display allocation frontier changed")
    expect(tuple(driver.LiveValue for driver in live) == (request["count"], request["pitch"])
           and all(driver.DisplayValue.FieldsValue["n2b0"] == 0 and not driver.DisplayValue.FieldsValue["f2b0"]
                   for driver in idle), "active drivers or dormant display memberships disagree")
    d1 = count.DisplayValue.FieldsValue
    d3 = pitch.DisplayValue.FieldsValue
    dimension = pitch.DimensionValue.FieldsValue
    matrix, offset = ReadRigidXform(dimension["ff0"])
    measured_span = dist(first, second)
    expect(words(matrix + offset) == words(inverse(first, axis))
           and dimension["has_fe0"] == dimension["has_ff0"] == 1
           and words(vector(dimension["fe0"])) == words(AXES[axis])
           and words(vector(dimension["fe8"])) == words(Z)
           and vector(dimension["f80"]) == first and vector(dimension["fa0"]) == second
           and vector(dimension["fc0"]) == ZERO and dimension["pt_flags"] == 0,
           "actual D3 geometry and inverse frame differ from its independent selection")
    for name, point in (("f880", (0.0, 1.0, 0.0)), ("fa38", (1.0, 0.0, 0.0)),
                        ("f988", (measured_span, 0.0, 0.0)), ("f9a0", (measured_span, 0.0, 0.0)),
                        ("f958", ZERO), ("f970", ZERO), ("f9b8", ZERO)):
        expect(vector(d3[name]) == point, f"wrong D3 adornment {name}")
    expect(d1["fad0"] == float(count.LiveValue) and d3["fad0"] == measured_span
           and d3["f8b0"] == 0.0 and d3["f8a8"] == request["midpoint"]
           and vector(d1["f6a0"]["f38"]) == tuple(request["count_label"])
           and vector(d3["f6a0"]["f38"]) == ZERO
           and count.DimensionValue.FieldsValue["has_ff0"] == 0,
           "count or pitch display cache differs from independent parameters and style")
    return {
        "seed_and_sketch": [seed.IndexValue, sketch.IndexValue],
        "display_frontier": fields["fd44"],
        "catalog_ids": {name: view.FieldsValue["f360"] for name, view in registrations.items()},
        "active_views": {driver.NativeName: [name, driver.DisplayValue.FieldsValue["f2b0"][0]["v"]]
                         for driver, name in zip(live, names, strict=True)},
        "slots": {driver.NativeName: {
            "owner_map": [node.IndexValue for node in (driver.DisplayValue, driver.HandleValue,
                                                      driver.DimensionValue, driver.ParameterValue)],
            "dimension_id": driver.DimensionValue.FieldsValue["f50"],
            "display_id": driver.DisplayValue.FieldsValue["f58"], "value": driver.LiveValue,
            "display_cache": driver.CacheValue, "label": vector(driver.DisplayValue.FieldsValue["f6a0"]["f38"]),
            "style_word": driver.DisplayValue.FieldsValue["f8a4"],
        } for driver in (count, pitch, *idle)},
        "pitch_witnesses_m": [first, second],
        "pitch_frame_words": [value.hex() for value in matrix + offset],
        "pitch_midpoint_word": d3["f8a8"].hex(),
        "pitch_local_extent_m": measured_span,
    }


def replay(link, header, config, resolved):
    found, written = WriteConfigMut(link.ConfigValue.RootValue, VERSION, header)
    regenerated, graph = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                       VERSION, written.MapValue, link.ResolvedValue.ContextValue)
    expect(found == config and regenerated == resolved and written.MapValue == link.ConfigValue.MapValue
           and graph.MapValue == link.ResolvedValue.MapValue, "complete linked Config/Resolved streams or maps differ")
    return {"config": digest(config), "resolved": digest(resolved),
            "stream_lengths": [len(config), len(resolved)],
            "map": [written.MapValue.CounterValue, graph.MapValue.CounterValue]}


def source_probe(request, raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    header = link.ConfigValue.HeaderValue
    node = link.ResolvedValue.RootsValue[-1]
    second = ReadHeaderGraph(archive.require("Header2"), VERSION)
    direction = line_owner(node.FieldsValue["f1288"], link.ResolvedValue.RootsValue, link.ConfigValue, (header, second))
    expect(direction["plane_role"] == (1 if request["axis"] == "x" else 2)
           and node.FieldsValue["f1298"] == int(request["axis"] == "y"), "source principal direction changed")
    return inspect_drivers(link, request) | replay(link, header, archive.require(link.ConfigName),
                                                   archive.require(link.StreamName)) | {"archive_sha256": digest(raw)}


def model_probe(request, _):
    axis, name, epoch = (request[key] for key in ("axis", "name", "epoch"))
    plate, seed = (tuple(tuple(map(float, row)) for row in request[key]) for key in ("plate", "seed"))
    count, pitch = request["count"], request["pitch"]
    stock = MakePatternSeed(SeedStockInput(name, "Default", f"C:\\KitPrincipalPattern\\{name}.SLDPRT", epoch,
                                           FrontStockBox("PlateSketch", "PlateBoss", plate),
                                           FrontStockBox("SeedSketch", "SeedBoss", seed)))
    reverse = request.get("reverse", axis == "y")
    _ = MakePatBoxes(plate, seed, AXES[axis], pitch, count)
    system, allocator = stock.SystemValue, stock.Allocator
    model = system.RootValue
    PutHingeViews(system, stock.BoundsValue)
    plane = system.SystemValues.PlaneValues[axis]
    order = request["order"]
    variants = request.get("contrast")
    view_inputs = tuple(AnnoViewInput(name, BASIS["*Front" if variants == "wrong_basis" and name == PITCH_VIEW[axis] else name])
                        for name in order if variants != "missing_view" or name != PITCH_VIEW[axis])
    PutAnnoCatalog(model, VERSION, view_inputs, None, (None,))
    names = {"D1": "*Front", "D3": PITCH_VIEW[axis]}
    labels = {"D1": tuple(request["count_label"]), "D2": seed[0], "D4": tuple(request["idle_label"])}
    styles = tuple(PatDriveStyle(name, names.get(name), labels.get(name, ZERO), True, 0)
                   for _, name, _ in KPatDriveSlots)
    pattern = MakePatFeature(stock, "LinearPattern")
    if variants == "wrong_style":
        styles = (styles[0], replace(styles[1], AnnotationName="*Front"), *styles[2:])
    if variants == "foreign_seed":
        pattern.FieldsValue["f988"].FieldsValue["items"][0]["o"] = stock.PlateValue.FeatureValue
    if variants == "detached_plane":
        plane = ArchiveNode(plane.ClassValue, dict(plane.FieldsValue))
    before = dict(allocator.Allocations)
    try:
        constructed = PutPrincMut(stock, pattern, plane, styles, count, pitch, reverse)
    except ValueError:
        expect(before == allocator.Allocations and model.FieldsValue["fd44"] == 10
               and all(key not in pattern.FieldsValue for key, _, _ in KPatDriveSlots),
               "failed principal display construction consumed a driver or display identity")
        raise
    expect(all(driver.ParameterValue.FieldsValue["owner"] is pattern
               and driver.DimensionValue.FieldsValue["owner"] is pattern
               and driver.DisplayValue.FieldsValue["owner"] is pattern
               and driver.DimensionValue.FieldsValue["retaining_handles"] == (driver.HandleValue,)
               for driver in constructed), "constructed driver lost its real owning feature")
    line = MakePatDir(system, stock.SettingsValue, allocator, plane, MakeSeedHeaders(stock)[:2])
    FinishPatMut(stock, pattern, line, reverse)
    headers = MakeSeedHeaders(stock, pattern)
    header, peer = (ReadHeaderGraph(WriteHeadGraph(value, VERSION), VERSION) for value in headers[:2])
    config, written = WriteConfigMut(model, VERSION, header)
    manager = ReadCmgrMut(WriteCmgrMut(system.ManagerValue, VERSION), VERSION)
    read_config = ReadConfigMut(config, VERSION, header)
    context = MakeLinkContext(read_config, manager)
    body, emitted = WriteResolMut((*stock.RootsValue, pattern), None, VERSION, written.MapValue, context)
    resolved = ReadResolvedMut(body, VERSION, read_config.MapValue, context)
    link = NativeLink(read_config, resolved, "Contents/Config-0", "Contents/Config-0-ResolvedFeatures")
    decoded = RequireNative(resolved.RootsValue[-1], "moLPattern_c")
    _ = line_owner(decoded.FieldsValue["f1288"], resolved.RootsValue, read_config, (header, peer))
    expect(emitted.MapValue.CounterValue == resolved.MapValue.CounterValue
           and [(row.IndexValue, getattr(row.EntryValue, "ClassValue", row.EntryValue)) for row in emitted.MapValue.EntriesValue]
           == [(row.IndexValue, getattr(row.EntryValue, "ClassValue", row.EntryValue)) for row in resolved.MapValue.EntriesValue],
           "actual complete Resolved map lost an earlier object or class slot")
    first = seed[0]
    independent = request | {"first": first, "midpoint": placement(first, finish(first, pitch, axis), axis)}
    report = inspect_drivers(link, independent)
    expect(report["catalog_ids"] == {name: 200 + index for index, name in enumerate(order)}
           and report["slots"]["D2"]["label"] == seed[0] and report["slots"]["D4"]["label"] == tuple(request["idle_label"]),
           "generated archive lost explicit view registration or dormant presentation")
    return report | replay(link, header, config, body) | {"request_sha256": digest(wire(request))}


def launch(mode, request, raw=b"", refusal=None):
    header = json.dumps(request, allow_nan=False, sort_keys=True).encode() + b"\n"
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), cwd=ROOT, input=header + raw,
                 capture_output=True, check=False, timeout=60)
    if refusal:
        expect(result.returncode and not result.stdout and refusal in result.stderr.decode()
               and "consumed a driver" not in result.stderr.decode(), "wrong bounded principal driver refusal: " + result.stderr.decode())
        return result.stderr.decode().splitlines()[-1]
    expect(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return json.loads(result.stdout)


def sources(packet_root):
    packet = json.loads(pinned(packet_root / "Packet" / "Packet.json", PACKET_PIN))
    lock = json.loads(pinned(MEASUREMENTS / "LocalLinearPatternDisclosedSourceLock01.json", SOURCE_LOCK))
    expect(lock["passed"] and lock["cohort"] == "disclosed" and lock["packet_sha256"] == PACKET_PIN
           and lock["distinct_processes"] == lock["completed_native_phases"] == 14
           and lock["writer_output_count"] == 0 and all(row["passed"] for row in lock["controls"].values()),
           "original disclosed native source lifecycle changed")
    files = {row["path"]: row["sha256"] for row in packet["files"]}
    for name, expected in (SOURCE_TOOLS | {"DisclosedInputs02.json": SOURCE_SPEC}).items():
        expect(files[name] == expected, "exact source intents or original authors are absent from the measured packet")
        pinned(packet_root / "Packet" / name, expected)
    specs = json.loads(pinned(packet_root / "Packet" / "DisclosedInputs02.json", SOURCE_SPEC))
    cases = json.loads(pinned(MEASUREMENTS / "LocalLinearPatternDatumPlacement01.json", PLACEMENT_PIN))["principal"]
    expected = {}
    for spec, case in zip(specs["cases"], lock["cases"], strict=True):
        name = spec["name"]
        expect(name == case["name"] and name in ("D01X", "D02Y") and case["passed"]
               and spec["split"] == case["split"] == "disclosed", "unexpected principal source role")
        axis = "x" if name == "D01X" else "y"
        first = tuple(((origin + offset + size / 2) * 1000) / 1000 - size * 1000 / 2000
                      for origin, offset, size in zip(spec["plate_origin_m"], spec["seed_offset_m"],
                                                      spec["seed_size_m"], strict=True)) + (0.0,)
        original = finish(first, spec["spacing_m"], axis)
        for member in case["native_sources"]:
            file = member["name"]
            suffix = file[len(name):-7]
            expect(file in cases and suffix in ("", "Spacing", "Instances")
                   and member["sha256"] == cases[file]["sha256"], "disclosed original or edit hash differs")
            request = {"axis": axis, "first": first, "count_label": original, "midpoint": placement(first, original, axis),
                       "count": spec["edit_instances"] if suffix == "Instances" else spec["instances"],
                       "pitch": spec["edit_spacing_m"] if suffix == "Spacing" else spec["spacing_m"]}
            raw = pinned(packet_root / "DisclosedNative" / name / file, member["sha256"])
            expect(len(raw) == member["bytes"], "source artifact size changed")
            expected[file] = launch("source", request, raw)
        pristine, count, pitch = (expected[name + suffix + ".SLDPRT"] for suffix in ("", "Instances", "Spacing"))
        for edited in (count, pitch):
            expect(all(pristine["slots"][role][field] == edited["slots"][role][field]
                       for role in ("D2", "D4", "D5", "D6")
                       for field in pristine["slots"][role] if field != "style_word")
                   and pristine["slots"]["D2"] == edited["slots"]["D2"]
                   and pristine["active_views"] == edited["active_views"]
                   and pristine["pitch_frame_words"] == edited["pitch_frame_words"]
                   and all(edited["slots"][role]["style_word"] ^ pristine["slots"][role]["style_word"] == 0x02000000
                           for role in ("D3", "D4", "D5", "D6")),
                   "native edit changed dormant owners, view registration, pitch frame or expected display flag")
    expect(len(expected) == 6, "principal source disclosures are incomplete")
    return expected


def modeled():
    base_cases = {
        "right": {"axis": "x", "name": "NewRightPitch", "epoch": 1795590051,
                  "plate": [[0, 0, 0], [0.153, 0.099, 0.011]], "seed": [[0.019, 0.0183, 0], [0.0265, 0.0272, 0.034]],
                  "count": 4, "pitch": 0.0217, "order": ["*Front", "*Top"], "count_label": [0.06797, 0.0351, 0.0],
                  "idle_label": [0.02012, 0.03937, 0.0]},
        "top": {"axis": "y", "name": "NewTopPitch", "epoch": 1795590063,
                "plate": [[0, 0, 0], [0.151, 0.17, 0.014]], "seed": [[0.052, 0.109, 0], [0.0615, 0.116, 0.029]],
                "count": 4, "pitch": 0.02137, "order": ["*Left", "*Top", "*Front"], "count_label": [0.0552, 0.08781, 0.0],
                "idle_label": [0.031, 0.112, 0.0]},
    }
    results = {}
    for name, initial in base_cases.items():
        results[name] = {role: launch("model", request)
                         for role, request in (("initial", initial), ("count", initial | {"count": 5}),
                                               ("pitch", initial | {"pitch": 0.01893}))}
        first, count, pitch = (results[name][role] for role in ("initial", "count", "pitch"))
        expect(first == launch("model", initial) and count["slots"]["D3"] == first["slots"]["D3"]
               and pitch["slots"]["D1"] == first["slots"]["D1"]
               and all(same["slots"][role] == first["slots"][role] for same in (count, pitch) for role in ("D2", "D4", "D5", "D6"))
               and first["config"] == count["config"] == pitch["config"]
               and len({value["resolved"] for value in (first, count, pitch)}) == 3,
               "model edit changed a dormant owner or unrelated driver and view registry")
    right, top = base_cases["right"], base_cases["top"]
    failures = {
        "wrong_style": launch("model", right | {"contrast": "wrong_style"}, refusal="Front count and its signed pitch view"),
        "wrong_basis": launch("model", top | {"contrast": "wrong_basis"}, refusal="actual canonical annotation frame"),
        "missing_view": launch("model", top | {"contrast": "missing_view"}, refusal="actual authored annotation view"),
        "foreign_seed": launch("model", right | {"contrast": "foreign_seed"}, refusal="its actual rectangular Front seed"),
        "detached_plane": launch("model", top | {"contrast": "detached_plane"}, refusal="actual registered principal plane"),
        "alternate_sense": launch("model", right | {"reverse": True}, refusal="measured signed Right or Top direction"),
    }
    return results, failures


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--packet-root", type=Path)
    modes.add_argument("--worker", choices=("source", "model"))
    args = parser.parse_args()
    if args.worker:
        request = json.loads(sys.stdin.buffer.readline())
        raw = sys.stdin.buffer.read()
        for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
            lookup(name)
        audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
        sys.addaudithook(audit.InspectEvent)
        audit.BeginBuild()
        report = (source_probe if args.worker == "source" else model_probe)(request, raw)
        expect(not audit.DeniedReads, "principal driver probe reopened a runtime input")
        sys.stdout.buffer.write(wire(report | {"runtime_file_reads": 0}))
        return
    historical = sources(args.packet_root)
    generated, failures = modeled()
    sys.stdout.buffer.write(wire({
        "schema": "kit.sw2026.principal-pattern-drivers.v1", "base": BASE, "native_build": "34.5.2.0604",
        "source_lock_sha256": SOURCE_LOCK, "source_spec_sha256": SOURCE_SPEC, "source_packet_sha256": PACKET_PIN,
        "source_tool_sha256": SOURCE_TOOLS,
        "source_placement_sha256": PLACEMENT_PIN, "disclosed": historical, "generated": generated,
        "refusals": failures, "guarded_workers": 20, "new_native_launches": 0, "heldout_inputs_read": 0,
        "writer_files_published": 0, "tool_sha256": digest(HERE.read_bytes()),
    }))


if __name__ == "__main__":
    main()
