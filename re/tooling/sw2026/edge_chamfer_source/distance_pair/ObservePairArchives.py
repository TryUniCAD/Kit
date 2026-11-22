from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path
from struct import unpack
import sys


VERSION = 19000
BUILD = "34.5.2.0604"
EXECUTABLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCES = {
    "equal": ("EqualDistanceEdge", "d8ff6c2678c05c88f52a3d10e10e1ccdd84fb52a9b374bf7542be868f4215390",
              0x12, ("f810",), ("shared",), (4.875,), (6.125,)),
    "unequal": ("UnequalDistanceEdge", "d1892bc383b88c4d0b4a48d2fa768c2274a70f755068e218a28ca6475fb45b51",
                0x02, ("f810", "f820"), ("first", "second"), (4.875, 8.375), (4.875, 9.625)),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def identity(data):
    return sha256(data).hexdigest()


def guard():
    observed = []
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)

    def deny(event, _):
        if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            observed.append(event)
            raise ValueError(f"distance pair replay attempted external access: {event}")

    sys.addaudithook(deny)
    return observed


def snapshot(args):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import ChmfRoleKey, EdgeChmfRows
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
    from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    name, terminal_pin, word, slots, roles, before, after = SOURCES[args.case]
    terminal_raw = (args.capture / "Result.json").read_bytes()
    require(identity(terminal_raw) == terminal_pin, "disclosed native receipt has the wrong hash")
    terminal = loads(terminal_raw)
    require(terminal["oracle_build"] == BUILD and terminal["oracle_sha256"] == EXECUTABLE
            and terminal["control_before"]["passed"] and terminal["control_after"]["passed"],
            "disclosed native receipt has the wrong build or controls")
    (case,) = [row for row in terminal["cases"] if row["case"] == name and row["passed"]]
    expected = case["edited_sha256"] if args.edited else case["original_sha256"]
    raw = (args.capture / name / (name + ("Edited" if args.edited else "") + ".SLDPRT")).read_bytes()
    require(identity(raw) == expected, "disclosed mode source has the wrong hash")
    denied = guard()
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    config, resolved = link.ConfigValue, link.ResolvedValue
    roots = resolved.RootsValue
    require(sum(node is not None and node.ClassValue.NameValue == "Chamfer_c" for node in roots) == 1,
            "archive has overlapping chamfer roots")
    feature = RequireNative(roots[-1], "Chamfer_c")
    fields = feature.FieldsValue
    require(fields["f8c0"] == word and fields["f8a0"] == 10
            and {slot for slot in ("f810", "f818", "f820", "f828", "f830", "f838") if fields[slot] is not None}
            == set(slots), "disclosed chamfer mode and actual display roots differ")
    drivers = {}
    compiled = []
    for slot, role, mm in zip(slots, roles, after if args.edited else before, strict=True):
        display = RequireNative(fields[slot], "moDisplayDistanceDim_c")
        dim, parameter, actual = ReadPrismParam(display, False)
        (handle_row,) = NativeRows(display.FieldsValue["f850"])
        handle = RequireNative(handle_row["o"], "moFeatureDimHandle_c")
        cell = display.FieldsValue["f5b0"]
        native_name = ReadNativeName(parameter)
        require(native_name == case["drivers"][role][0]
                and isclose(actual, mm / 1000, rel_tol=0.0, abs_tol=1e-14)
                and cell["elem"] == 8 and cell["n"] == 1 and unpack("<d", cell["data"])[0] == actual,
                "archive driver does not match the actual native source and independent edit")
        owners = (display, handle, dim, parameter)
        compiled += owners
        drivers[role] = {"name": native_name, "value_si": actual, "field": slot, "persistent_id": dim.FieldsValue["f50"],
                         "owners": [dict(NativeNodeSpan(link, owner)) for owner in owners]}
    require(len(set(compiled)) == len(compiled)
            and len({row["persistent_id"] for row in drivers.values()}) == len(drivers),
            "distance-pair driver roots are not independently owned")
    CheckTreeAlias(link, (feature, *compiled))
    manager_path = "Contents/CMgr"
    manager = ReadCmgrMut(archive.require(manager_path), VERSION)
    config_wire, written = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    resolved_wire, written_resolved = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, VERSION, written.MapValue, MakeLinkContext(written, manager),
        WriteChamfers=True,
    )
    replays = {link.ConfigName: config_wire, link.StreamName: resolved_wire, manager_path: WriteCmgrMut(manager.RootValue, VERSION)}
    require(all(wire == archive.require(lane) for lane, wire in replays.items())
            and (written.MapValue.CounterValue, written_resolved.MapValue.CounterValue)
            == (config.MapValue.CounterValue, resolved.MapValue.CounterValue) and not denied,
            "distance pair archives did not replay without input reads")
    selected = RequireNative(fields["f8a8"], "moCompEdge_c")
    edge = RequireNative(selected.FieldsValue["fe8"], "moEdgeRef_c")
    return {"case": args.case, "edited": args.edited, "source_sha256": expected,
            "native_terminal_sha256": terminal_pin, "build": BUILD, "mode_word": word,
            "mode_fields": {field: fields[field] for field in ("f860", "f8a0", "f878", "f87c", "has_f808", "f8f0")},
            "feature": dict(NativeNodeSpan(link, feature)), "drivers": drivers,
            "selected_edge": dict(NativeNodeSpan(link, selected)),
            "ordered_edge_roles": [ChmfRoleKey(row) for row in EdgeChmfRows(edge)],
            "edge_flip_flags": fields["f8c8"],
            "map_counters": [config.MapValue.CounterValue, resolved.MapValue.CounterValue],
            "stream_replays": {lane: [len(wire), identity(wire)] for lane, wire in replays.items()},
            "exact_replay": True, "guarded_input_reads": len(denied), "heldout_sources_read": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--case", choices=SOURCES, required=True)
    parser.add_argument("--edited", action="store_true")
    args = parser.parse_args()
    require(sys.platform == "win32" and args.capture.is_absolute() and args.capture.drive.casefold() == "c:",
            "disclosed source archives must remain on guest-local C:")
    sys.path.insert(0, str(args.source_tree.resolve()))
    print(dumps(snapshot(args), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
