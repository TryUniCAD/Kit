from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgCaches import DISCLOSED_CASES, NATIVE_CASES, audit_run, context_entries, inspect, require
from ReadWirePartCaches import PRE_FIELDS, author_mass_wire, author_one_slot
from convert.adapters.solidworks.Archive.Config.Caches.ReadCfgCache import ReadCfgCache
from convert.adapters.solidworks.Archive.Config.Caches.WriteCfgCache import WriteCfgCache
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(data):
    return sha256(data).hexdigest()


def audit_guard():
    for name in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(name)
    state = {"active": True, "denied": []}

    def guard(event, arguments):
        if state["active"]:
            try:
                audit_run(event, arguments)
            except PermissionError:
                state["denied"].append(event)
                raise

    sys.addaudithook(guard)
    return state


def comparison(fields, wire, seed, part, kind):
    original_model = deepcopy(fields)
    before = (seed.CounterValue, tuple(id(entry) for entry in seed.EntriesValue), part.FieldsValue.copy())
    output = WriteCfgCache(fields, 19000, seed, part, kind)
    require(output == wire and fields == original_model, "cache bytes or caller model changed")
    decoded = inspect(output, 19000, seed, part, kind)
    after = (seed.CounterValue, tuple(id(entry) for entry in seed.EntriesValue), part.FieldsValue)
    require(before == after, "owned model or seed mutated")
    return {"bytes": len(output), "sha256": digest(output), "fields_sha256": decoded["fields_sha256"],
            "map_counter": decoded["counter"], "anchor_slots": decoded["anchor_slots"],
            "exact_byte_identity": True}


def native_case(case, directory):
    relative, file_sha, config_sha, header_sha, mass, bounds = (NATIVE_CASES | DISCLOSED_CASES)[case]
    path = directory / relative
    raw = path.read_bytes()
    require(digest(raw) == file_sha, "unexpected native cache source")
    archive = SldprtArchive.from_bytes(raw)
    version = ContainerMo(archive.streams)
    require(version == 19000 and archive.format_version == 4, "unexpected native cache version")
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require((digest(config), digest(header)) == (config_sha, header_sha), "unexpected source control streams")
    part, entries = context_entries(config, header, version)
    guard = audit_guard()
    values = {}
    for kind, (start, end, counter, pin) in (("mass", mass), ("bounds", bounds)):
        wire = config[start:end]
        require(digest(wire) == pin, "unexpected measured cache interval")
        seed = MapSnapshot(counter, entries)
        model = ReadCfgCache(wire, version, seed, part, kind)
        values[kind] = comparison(dict(model.FieldsValue), wire, seed, part, kind)
        values[kind]["native_interval"] = [start, end]
    guard["active"] = False
    require(not guard["denied"] and digest(path.read_bytes()) == file_sha, "cache guard or source custody failed")
    return {"case": case, "source_sha256": file_sha, "config_sha256": config_sha, "header_sha256": header_sha,
            "records": values, "runtime_external_accesses": 0}


def mass_props():
    fields = dict(zip(PRE_FIELDS, (
        *[0.25 + index / 8 for index in range(12)],
        4, -8, 16, -32, 64, 0.5, 6, 7, 8, 9,
    ), strict=True))
    fields.update({
        "f148": ("A", "rendered cache"), "f150": "edited β", "f1f0": -3,
        "fc8": 0.0, "fd0": 0.25, "fd8": 0.5,
        "f68": dict(x=0.75, y=1.0, z=1.25),
        "f80": dict(x=1.5, y=1.75, z=2.0),
        "f98": dict(x=2.25, y=2.5, z=2.75),
        "f15c": -6, "f128": 7,
    })
    return fields


def refuse(fields, seed, part, kind, expected, version=19000):
    try:
        WriteCfgCache(fields, version, seed, part, kind)
    except ValueError as error:
        require(expected in str(error), f"wrong cache refusal: {error}")
    else:
        raise ValueError("unqualified cache emitted bytes")


def authored_case():
    desc = RuntimeClass("moPart_c", 1)
    part = ArchiveNode(desc, {})
    seed = MapSnapshot(41, (MapEntry(1, desc), MapEntry(2, part)))
    one = {"f1628": [{"f08": [{"atom": 211, "v": -40, "d": 0.625}], "f18": mass_props()}], "f1638": 0}
    two = {"f1628": [{"f08": []}, {"f08": [{"atom": 101, "v": -5, "d": 0.125},
                                         {"atom": 103, "v": 7, "d": 0.875}], "f18": mass_props()}], "f1638": -17}
    empty = {"f1628": [], "f1638": 0}
    bounds = {"f1640": []}
    guard = audit_guard()
    values = {
        "empty_mass": comparison(empty, pack("<i", 0), seed, part, "mass"),
        "one_slot": comparison(one, author_one_slot(), seed, part, "mass"),
        "two_slots": comparison(two, author_mass_wire(), seed, part, "mass"),
        "empty_bounds": comparison(bounds, pack("<i", 0), seed, part, "bounds"),
    }
    changed = deepcopy(two)
    changed["f1638"] = -23
    values["changed_selector"] = comparison(changed, author_mass_wire()[:-4] + pack("<i", -23),
                                            seed, part, "mass")
    extra_atom = deepcopy(one)
    extra_atom["f1628"][0]["f08"][0]["owner"] = 211
    missing_member = deepcopy(one)
    del missing_member["f1628"][0]["f18"]["f20"]
    extra_vector = deepcopy(one)
    extra_vector["f1628"][0]["f18"]["f68"]["units"] = "m"
    cases = (
        ("extra_slot", {"f1628": [{"f08": []}] * 3, "f1638": 0}, seed, part, "mass", "outside zero through two", 19000),
        ("inactive_selector", {**one, "f1638": -23}, seed, part, "mass", "selector requires two slots", 19000),
        ("missing_selector", {"f1628": two["f1628"]}, seed, part, "mass", "exactly its modeled fields", 19000),
        ("inactive_property", {"f1628": [{"f08": [], "f18": mass_props()}], "f1638": 0}, seed, part, "mass", "property requires atom rows", 19000),
        ("absent_property", {"f1628": [{"f08": [{"atom": 211, "v": -40, "d": 0.625}]}], "f1638": 0}, seed, part, "mass", "property requires atom rows", 19000),
        ("missing_atom_rows", {"f1628": [{"n10": 0}], "f1638": 0}, seed, part, "mass", "slot has unmodeled fields", 19000),
        ("unmodeled_atom", extra_atom, seed, part, "mass", "atom row has unmodeled fields", 19000),
        ("missing_property_member", missing_member, seed, part, "mass", "property has unmodeled fields", 19000),
        ("unmodeled_vector", extra_vector, seed, part, "mass", "vector has unmodeled fields", 19000),
        ("populated_bounds", {"f1640": [{"k": 7, "o": None}]}, seed, part, "bounds", "requires typed owners", 19000),
        ("missing_owner", empty, seed, ArchiveNode(desc, {}), "mass", "mapped ordinary part", 19000),
        ("wrong_version", empty, seed, part, "mass", "requires archive version 19000", 18900),
        ("unsupported_kind", {}, seed, part, "other", "unsupported SOLIDWORKS configuration cache field", 19000),
    )
    for _, *parameters in cases:
        refuse(*parameters)
    require(not guard["denied"], "authored encoder attempted external access")
    return {"case": "authored", "runtime_external_accesses": 0, "records": values,
            "refusals": [label for label, *_ in cases]}


def supervisor(disclosed):
    results = []
    plans = ("ladder", "concave", "authored")
    if disclosed is not None:
        plans += ("circle", "polygon")
    for case in plans:
        args = (sys.executable, "-I", "-B", str(HERE), case)
        if case in DISCLOSED_CASES:
            args += ("--disclosed-root", str(disclosed))
        measured = run(args, capture_output=True, timeout=60, check=False)
        require(measured.returncode == 0 and not measured.stderr, measured.stderr.decode()[-2500:])
        results.append(json.loads(measured.stdout))
    return {"schema": "kit.sw2026.config-cache-write.v1", "guarded_fresh_processes": len(results),
            "native_processes_started": 0, "runtime_external_accesses": sum(row["runtime_external_accesses"] for row in results),
            "native_oracle_qualified": False, "cases": results}


def main():
    parser = ArgumentParser()
    parser.add_argument("case", choices=(*NATIVE_CASES, *DISCLOSED_CASES, "authored", "measure"))
    parser.add_argument("--disclosed-root", type=Path)
    args = parser.parse_args()
    if args.case == "measure":
        result = supervisor(args.disclosed_root)
    elif args.case == "authored":
        result = authored_case()
    else:
        if args.case in DISCLOSED_CASES and args.disclosed_root is None:
            parser.error("the native control requires its disclosed root")
        result = native_case(args.case, args.disclosed_root if args.case in DISCLOSED_CASES else ROOT)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
