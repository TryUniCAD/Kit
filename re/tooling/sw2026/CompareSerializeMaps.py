from __future__ import annotations

import argparse
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path


def unique_mapping(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate map member {key!r}")
        result[key] = value
    return result


def module_name(value):
    if not isinstance(value, str) or not value or not value.isascii() or value.strip() != value:
        raise ValueError("each map entry must have a module name")
    stem = value.casefold().removesuffix(".dll")
    if not stem or not all(char.isalnum() or char in "-_" for char in stem):
        raise ValueError(f"invalid module name {value!r}")
    return stem + ".dll"


def read_map(path, fallback):
    raw = path.read_bytes()
    values = json.loads(raw, object_pairs_hook=unique_mapping)
    if not isinstance(values, dict) or not values:
        raise ValueError(f"{path.name} must contain a nonempty class map")
    fallback = None if fallback is None else module_name(fallback)
    primary_counts = Counter()
    alternate_counts = Counter()
    modules = {}
    for name, primary in values.items():
        if not name or not isinstance(primary, dict):
            raise ValueError(f"invalid class entry {name!r}")
        variants = primary.get("also", [])
        if not isinstance(variants, list):
            raise ValueError(f"invalid alternate entries for {name!r}")
        for index, entry in enumerate((primary, *variants)):
            if not isinstance(entry, dict):
                raise ValueError(f"invalid serializer entry for {name!r}")
            module = module_name(entry.get("dll", fallback if index == 0 else None))
            address = entry.get("serialize_addr")
            symbol = entry.get("serialize_name")
            slots = entry.get("vtable_slots")
            if not isinstance(address, str) or not isinstance(symbol, str) or not symbol:
                raise ValueError(f"invalid serializer target for {name!r} in {module}")
            address = int(address, 16)
            if address <= 0 or slots is not None and (type(slots) is not int or slots < 1):
                raise ValueError(f"invalid serializer inventory for {name!r} in {module}")
            entries = modules.setdefault(module, {})
            if name in entries:
                raise ValueError(f"ambiguous serializer entry for {name!r} in {module}")
            entries[name] = address, symbol, slots
            counts = alternate_counts if index else primary_counts
            counts[module] += 1
    inventory = {
        "map_name": path.name,
        "sha256": sha256(raw).hexdigest(),
        "default_module_for_flat_map": fallback,
        "primary_classes": len(values),
        "primary_entries_by_module": dict(sorted(primary_counts.items())),
        "alternate_entries_by_module": dict(sorted(alternate_counts.items())),
    }
    return inventory, modules


def module_difference(before, after):
    shared = sorted(before.keys() & after.keys())
    slots_changed = []
    slots_unavailable = []
    for name in shared:
        older_slots = before[name][2]
        newer_slots = after[name][2]
        if older_slots is None or newer_slots is None:
            slots_unavailable.append(name)
        elif older_slots != newer_slots:
            slots_changed.append({"class": name, "older": older_slots, "newer": newer_slots})
    return {
        "older_entries": len(before),
        "newer_entries": len(after),
        "shared_classes": len(shared),
        "older_only_classes": sorted(before.keys() - after.keys()),
        "newer_only_classes": sorted(after.keys() - before.keys()),
        "vtable_slot_count_changes": slots_changed,
        "vtable_slot_count_unavailable": slots_unavailable,
        "serializer_address_differences": sum(before[name][0] != after[name][0] for name in shared),
        "serializer_name_spelling_differences": sum(before[name][1] != after[name][1] for name in shared),
    }


def compare(older, newer, *, older_default_module=None, newer_default_module=None):
    older_inventory, before = read_map(older, older_default_module)
    newer_inventory, after = read_map(newer, newer_default_module)
    return {
        "schema": "kit.solidworks.serialize-map-diff.v1",
        "older": older_inventory,
        "newer": newer_inventory,
        "modules_sampled_only_in_older": {module: len(before[module]) for module in sorted(before.keys() - after.keys())},
        "modules_sampled_only_in_newer": {module: len(after[module]) for module in sorted(after.keys() - before.keys())},
        "shared_modules": {module: module_difference(before[module], after[module]) for module in sorted(before.keys() & after.keys())},
        "wire_changes_verified_by_comparison": [],
    }


def main():
    parser = argparse.ArgumentParser(description="Compare two local SOLIDWORKS serializer inventories")
    parser.add_argument("older", type=Path)
    parser.add_argument("newer", type=Path)
    parser.add_argument("--older-default-module", help="module for entries without a DLL in the older inventory")
    parser.add_argument("--newer-default-module", help="module for entries without a DLL in the newer inventory")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="write the deterministic comparison receipt")
    mode.add_argument("--check", type=Path, help="verify an existing receipt byte for byte")
    args = parser.parse_args()
    try:
        comparison = compare(args.older, args.newer, older_default_module=args.older_default_module, newer_default_module=args.newer_default_module)
        encoded = (json.dumps(comparison, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if args.check is not None:
            if args.check.read_bytes() != encoded:
                parser.error(f"comparison differs from {args.check}")
        else:
            if args.output.resolve() in (args.older.resolve(), args.newer.resolve()):
                parser.error("comparison output must be separate from both input maps")
            args.output.write_bytes(encoded)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
