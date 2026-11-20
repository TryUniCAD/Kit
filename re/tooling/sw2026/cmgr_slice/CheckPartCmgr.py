from argparse import ArgumentParser
from codecs import lookup
from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
from subprocess import check_output
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = (str(ROOT / "src"), str(Path(__file__).resolve().parent))

from PartCmgr import (
    BASE, CONFIGURATION, DESCRIPTORS, LAYOUTS, NAME, ArchiveNode, RuntimeClass,
    emit_graph, load_grammar, part_owner, read_manager, require, write_manager,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

STREAM = "Contents/CMgr"
VERSION = 19000
CORPUS = "re/solidworks/v2026/corpus/"
GENERATED_STREAM = "36a20801154a5ae2964c2c522a4edf62b280a87bf2b113e120fa6401f5d8e4fd"
SOURCES = {
    "l1": (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "599e3fea664a9788e402297ed0997b680efbf72cfc8a714abe6a8a140ef2d541", 2159, 19, 31,
    ),
    "concave": (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        GENERATED_STREAM, 1129, 10, 19,
    ),
    "rectangular": (
        "local-import-readback/RectangularBare.SLDPRT",
        "302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357",
        GENERATED_STREAM, 1129, 10, 19,
    ),
}
CASES = {
    "l1": "l1", "concave": "concave", "rectangular": "rectangular",
    "add-name": "l1", "remove-name": "concave", "refuse": "l1",
}


def digest(value):
    return sha256(value).hexdigest()


def read_source(case):
    path, source_hash, *_ = SOURCES[case]
    raw = check_output(("git", "show", f"{BASE}:{CORPUS}{path}"), cwd=ROOT)
    require(digest(raw) == source_hash, "disclosed source digest changed")
    return raw


def audit(event, args):
    if (event in ("open", "os.system", "os.listdir", "os.scandir", "os.exec",
                 "os.fork", "os.forkpty", "os.posix_spawn", "ctypes.dlopen")
            or event.startswith(("socket.", "subprocess."))):
        raise RuntimeError(f"part manager attempted external access: {event}")


def reachable_nodes(root):
    pending = [root]
    seen = set()
    while pending:
        value = pending.pop()
        if isinstance(value, ArchiveNode) and value not in seen:
            seen.add(value)
            pending.extend(value.FieldsValue.values())
        elif isinstance(value, Mapping):
            pending.extend(value.values())
        elif isinstance(value, (list, tuple)):
            pending.extend(value)
    return seen


def inspect_graph(graph, data):
    root, snapshot, usage = graph
    config, names = part_owner(root)
    entries = snapshot.EntriesValue
    require([row.IndexValue for row in entries] == list(range(1, snapshot.CounterValue)),
            "part manager did not map every slot from base one")
    require(entries[0].EntryValue is root.ClassValue and entries[1].EntryValue is root
            and root.StartOffset == 0 and root.EndOffset == len(data),
            "part manager root does not own the full stream")
    descriptors = {row.EntryValue for row in entries if isinstance(row.EntryValue, RuntimeClass)}
    nodes = {row.EntryValue for row in entries if isinstance(row.EntryValue, ArchiveNode)}
    require(nodes == reachable_nodes(root) and config in nodes, "map omitted a reachable object")
    rows = []
    for entry in entries:
        value = entry.EntryValue
        if isinstance(value, RuntimeClass):
            require(value.NameValue in DESCRIPTORS and value.SchemaValue == 1,
                    "part manager mapped an unqualified descriptor")
            rows.append([entry.IndexValue, value.NameValue, 1])
        else:
            require(value.ClassValue in descriptors and entry.IndexValue == value.IndexValue
                    and 0 <= value.StartOffset < value.EndOffset <= len(data),
                    "part manager object has invalid descriptor or extent")
            rows.append([entry.IndexValue, value.ClassValue.NameValue, value.StartOffset, value.EndOffset])
    require(usage["completed"] and not usage["missing_schemas"] and not usage["provisional_schemas"],
            "part manager layout traversal did not complete")
    return names | {
        "bytes": len(data), "sha256": digest(data), "map_counter": snapshot.CounterValue,
        "map": rows, "config_slot": config.IndexValue,
        "layouts": list(usage["used_schemas"]), "actions": dict(usage["field_calls"]),
    }


def source_graph(case, data, grammar):
    _, _, want_hash, length, counter, count = SOURCES[case]
    original = read_manager(data, VERSION, grammar)
    observation = inspect_graph(original, data)
    require((observation["sha256"], observation["bytes"], observation["map_counter"],
             len(observation["layouts"])) == (want_hash, length, counter, count),
            "manager stream differs from its disclosed measurements")
    require((observation["name"] is None) == (case == "l1")
            and observation["configuration"] == "Default",
            "manager presence or actual directory name differs")
    emitted, usage = write_manager(original[0], VERSION, grammar)
    require(emitted == data and usage == original[2]
            and inspect_graph(read_manager(emitted, VERSION, grammar), emitted) == observation,
            "manager typed emission changed bytes, role, span, map or layout use")
    return original, observation


def author_names(case, graph, observation, grammar):
    old_root, old_map, _ = graph
    config, _ = part_owner(old_root)
    if case == "add-name":
        authored = ("Panel manager Ω", "Inspection α", "measured Δ face", "ALT-FRONT", "fixture note")
        next_slot, config_slot = 20, 6
    else:
        authored = (None, "Oblique setup", "trace comment 🧭", "B", "material free")
        next_slot, config_slot = 9, 4
    manager, name, comment, alternate, description = authored
    old_root.FieldsValue["f18"] = None if manager is None else ArchiveNode(NAME, {"f08": manager})
    config.FieldsValue["f18"].FieldsValue["f08"] = name
    config.FieldsValue.update(f4a8=comment, f498=alternate, f1f8=description)
    source_slots = [(entry.EntryValue, entry.IndexValue) for entry in old_map.EntriesValue
                    if isinstance(entry.EntryValue, ArchiveNode)]
    output, usage = write_manager(old_root, VERSION, grammar)
    reissued = read_manager(output, VERSION, grammar)
    report = inspect_graph(reissued, output)
    require((report["name"], report["configuration"], report["comment"],
             report["alternate_name"], report["description"]) == authored,
            "authored manager text did not survive in the actual row")
    require((report["map_counter"], report["config_slot"]) == (next_slot, config_slot)
            and config.IndexValue == observation["config_slot"]
            and old_map.CounterValue == observation["map_counter"]
            and all(node.IndexValue == slot for node, slot in source_slots),
            "manager emission did not recompute output map identities independently")
    require(usage == reissued[2] and write_manager(reissued[0], VERSION, grammar)[0] == output,
            "authored manager reissue did not remain byte exact")
    return {"source": observation, "edited": report}


def reject_body(label, operation, reason):
    try:
        operation()
    except (TypeError, ValueError) as error:
        require(reason in str(error), f"{label} refused for another reason: {error}")
        return {"case": label, "diagnostic": str(error)}
    raise ValueError(f"{label} unexpectedly accepted")


def class_tag(name, schema):
    raw = name.encode("ascii")
    return pack("<HHH", 0xFFFF, schema, len(raw)) + raw


def refusals(root, data, grammar):
    observed = [
        reject_body("version", lambda: read_manager(data, 18900, grammar), "version 19000"),
        reject_body("wrong_root", lambda: read_manager(class_tag("suObList", 1), VERSION, grammar), "unsupported root"),
        reject_body("wrong_schema", lambda: read_manager(class_tag("moConfigurationMgr_c", 2), VERSION, grammar), "unsupported root"),
        reject_body("truncated", lambda: read_manager(data[:-1], VERSION, grammar), "truncated"),
        reject_body("trailing", lambda: read_manager(data + b"\0", VERSION, grammar), "trailing bytes"),
    ]
    fields = root.FieldsValue
    del fields["f18"]
    observed.append(reject_body("missing_name", lambda: write_manager(root, VERSION, grammar), "name field is missing"))
    fields["f18"] = ArchiveNode(NAME, {"f08": ""})
    observed.append(reject_body("empty_name", lambda: write_manager(root, VERSION, grammar), "name object cannot be empty"))
    fields["f18"] = None
    config, _ = part_owner(root)
    unrelated = ArchiveNode(CONFIGURATION, dict(config.FieldsValue))
    fields["f360"] = unrelated
    observed.append(reject_body("foreign_selector_write", lambda: write_manager(root, VERSION, grammar), "selectors must alias"))
    malformed, _ = emit_graph(root, VERSION, grammar)
    observed.append(reject_body("foreign_selector_read", lambda: read_manager(malformed, VERSION, grammar), "selectors must alias"))
    fields["f360"] = config
    directory = fields["f370"]
    directory["items"].append({"o": unrelated})
    directory["n"] = fields["f40c"] = 2
    observed.append(reject_body("multiple_rows_write", lambda: write_manager(root, VERSION, grammar), "exactly one counted configuration"))
    malformed, _ = emit_graph(root, VERSION, grammar)
    observed.append(reject_body("multiple_rows_read", lambda: read_manager(malformed, VERSION, grammar), "exactly one counted configuration"))
    return observed


def main():
    parser = ArgumentParser(description="Replay the bounded part CMgr on the accepted SDK")
    parser.add_argument("case", choices=CASES)
    case = parser.parse_args().case
    check_output(("git", "diff", "--exit-code", BASE, "--", "src"), cwd=ROOT)
    require(not check_output(("git", "ls-files", "--others", "--exclude-standard", "--", "src"), cwd=ROOT),
            "untracked files are present in the accepted SDK tree")
    grammar = load_grammar(ROOT)
    require((len(grammar[0]), len(grammar[2])) == (len(LAYOUTS), len(DESCRIPTORS)),
            "part manager registry size differs")
    source_case = CASES[case]
    raw = read_source(source_case)
    for name in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(name)
    sys.addaudithook(audit)
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "disclosed source has an unsupported container or archive version")
    data = archive.require(STREAM)
    graph, observation = source_graph(source_case, data, grammar)
    if case == "refuse":
        result = {"refusals": refusals(graph[0], data, grammar)}
    elif case in ("add-name", "remove-name"):
        result = author_names(case, graph, observation, grammar)
    else:
        result = {"source": observation}
    print(json.dumps(result | {"case": case, "source_sha256": digest(raw),
          "runtime_external_attempts": 0}, ensure_ascii=True, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
