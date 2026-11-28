from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys


MODES = ("MillimeterGram", "CustomGram", "CustomKilogram")
KINDS = ("corner", "center")
SCHEMA = "kit.sw2026.document-mass-unit-typed-proof.v1"


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(root, relative, expected):
    path = root / relative
    require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root),
            "document unit artifact escapes its packet")
    raw = path.read_bytes()
    require(digest(raw) == expected, "document unit artifact hash changed")
    return raw


def flatten(value, node_type, prefix=()):
    if isinstance(value, node_type):
        fields = {"class": value.ClassValue.NameValue, "schema": value.ClassValue.SchemaValue, **value.FieldsValue}
        return flatten(fields, node_type, prefix)
    if isinstance(value, dict):
        return {key: cell for name, child in value.items()
                for key, cell in flatten(child, node_type, (*prefix, name)).items()}
    if isinstance(value, (tuple, list)):
        return {key: cell for index, child in enumerate(value)
                for key, cell in flatten(child, node_type, (*prefix, str(index))).items()}
    require(value is None or type(value) in (bool, int, float, str), "unmapped document unit field")
    return {".".join(prefix): value}


def differences(first, second):
    return {
        "added": {name: second[name] for name in sorted(second.keys() - first.keys())},
        "removed": {name: first[name] for name in sorted(first.keys() - second.keys())},
        "changed": {name: [first[name], second[name]] for name in sorted(first.keys() & second.keys())
                    if first[name] != second[name]},
    }


def examine(raw):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    storage = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(storage, 0)
    config = link.ConfigValue
    root = config.RootValue
    require(root.ClassValue.NameValue == "moPart_c", "unit state does not own an ordinary part")
    user_table = root.FieldsValue["f9b8"]
    analysis_table = root.FieldsValue["f9c0"]
    require(isinstance(user_table, ArchiveNode) and user_table.ClassValue.NameValue == "moUnitsTable_c"
            and analysis_table is None, "native preference experiment has another table owner")
    entries = user_table.FieldsValue["items"]
    by_class = {item["o"].ClassValue.NameValue: item["o"] for item in entries}
    require(len(entries) == len(by_class) == user_table.FieldsValue["n"] == 16,
            "unit table class ownership differs")
    fields = {name: flatten(node, ArchiveNode) for name, node in by_class.items()}
    flattened = {f"{name}.{key}": value for name, row in fields.items() for key, value in row.items()}
    definition_raw = storage.require("Contents/Definition")
    manager_raw = storage.require("Contents/CMgr")
    config_raw, context = WriteConfigMut(root, 19000, config.HeaderValue)
    resolved_raw, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                    19000, context.MapValue, link.ResolvedValue.ContextValue)
    checks = {
        "Contents/Definition": WriteModelDef(ReadModelDef(definition_raw, 19000).GraphValue).OutputValue == definition_raw,
        "Contents/CMgr": WriteCmgrMut(ReadCmgrMut(manager_raw, 19000).RootValue, 19000) == manager_raw,
        link.ConfigName: config_raw == storage.require(link.ConfigName),
        link.StreamName: resolved_raw == storage.require(link.StreamName),
    }
    require(all(checks.values()), "document unit proof cannot re-emit its four actual streams")
    return flattened, checks, {key: digest(value) for key, value in storage.streams.items()}


def main():
    args = ArgumentParser(description="Verify native document unit preference ownership through the complete SDK graph")
    args.add_argument("kit", type=Path)
    args.add_argument("packet_root", type=Path)
    args.add_argument("output", type=Path)
    args.add_argument("--packet-sha256", required=True)
    args.add_argument("--native-result-sha256", required=True)
    cfg = args.parse_args()
    sys.path.insert(0, str(cfg.kit.resolve(strict=True) / "src"))
    root = cfg.packet_root.resolve(strict=True)
    packet = json.loads(checked(root, "Packet.json", cfg.packet_sha256))
    native = json.loads(checked(root, "Inspection/Result.json", cfg.native_result_sha256))
    require(native["passed"] and native["controls_healthy"] and native["distinct_native_processes"] == 10,
            "document unit oracle has unfinished phases")
    require(native["packet_sha256"] == cfg.packet_sha256 and native["writer_outputs"] == 0
            and packet["writer_outputs"] == 0 and native["heldout_inputs_read"] == 0,
            "document unit input custody differs")
    report = {"schema": SCHEMA, "passed": False, "packet_sha256": cfg.packet_sha256,
              "native_result_sha256": cfg.native_result_sha256, "cases": {}, "qualified_writer": False}
    for kind, case in zip(KINDS, packet["cases"], strict=True):
        require(case["kind"] == kind, "document unit case ownership differs")
        author = native["phases"][kind + "/Author"]
        checked(root, f"Inspection/{kind}/Author/Record.json", author["record_sha256"])
        states, rows = {}, {}
        for mode in MODES:
            source = author["states"][mode]
            reopen = native["phases"][kind + "/Reopen" + mode]
            checked(root, f"Inspection/{kind}/Reopen{mode}/Record.json", reopen["record_sha256"])
            readback = reopen["states"][mode]
            require(readback["sha256"] == source["sha256"] and source["units"] == readback["units"],
                    "document units did not survive reopening the authentic save")
            raw = checked(root, f"Inspection/{kind}/Author/{mode}.SLDPRT", source["sha256"])
            states[mode], replay, streams = examine(raw)
            rows[mode] = {"sha256": source["sha256"], "bytes": len(raw), "stream_hashes": streams,
                          "exact_stream_replay": replay, "native_preferences": source["units"]}
        system = differences(states["MillimeterGram"], states["CustomGram"])
        mass = differences(states["CustomGram"], states["CustomKilogram"])
        primary_length = "moLengthUserUnits_c."
        nested_length = "moDensityUnits_c.fb8."
        nested_length_fields = {
            nested_length + name[len(primary_length):]: value
            for name, value in states["CustomGram"].items()
            if name.startswith(primary_length) and not name.startswith(primary_length + "fb8")
        }
        nested_length_fields.update({nested_length + "f88": 0.0, nested_length + "fb8": None})
        display_precision = rows["CustomGram"]["native_preferences"]["swUnitsLinearDecimalPlaces"]
        prior_display, updated_display = (round(case[key] * 1000, display_precision) for key in ("height_m", "depth_m"))
        system_ok = system == {
            "added": nested_length_fields,
            "removed": {},
            "changed": {
                "moDensityUnits_c.has_fb8": [0, 1],
                "moLengthUserUnits_c.f88": [prior_display, updated_display],
                "moUnitSysUnits_c.fb0": [4, 3],
            },
        }
        mass_ok = mass == {"added": {}, "removed": {}, "changed": {"moDensityUnits_c.fc4": [1, 2]}}
        report["cases"][kind] = {"states": rows, "system_delta": system, "mass_delta": mass,
                                 "density_length_matches_primary_format_with_neutral_cache_and_no_dual":
                                     system["added"] == nested_length_fields,
                                 "observed_primary_length_f88_matches_rounded_driver_values": [prior_display, updated_display],
                                 "system_transition_matches": system_ok, "mass_transition_matches": mass_ok,
                                 "user_table_field_count": len(states["CustomKilogram"])}
    targets_ok = all(row["system_transition_matches"] and row["mass_transition_matches"]
                     for row in report["cases"].values())
    report["passed"] = targets_ok
    with cfg.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"passed": report["passed"], "typed_files": 6, "result_sha256": digest(cfg.output.read_bytes())}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
