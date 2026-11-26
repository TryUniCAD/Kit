from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from
from subprocess import check_output
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFrameOwnMut import ReadFrameOwnMut
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag
from convert.adapters.solidworks.Container.Container import SldprtArchive

CORPUS = ROOT / "re/solidworks/v2026/corpus"
CASES = {
    "ladder": (CORPUS / "ladder/L1_boss.SLDPRT",
               "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"),
    "concave": (CORPUS / "local-import-readback/ConcaveOwned.SLDPRT",
                "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33"),
    "bare": (CORPUS / "local-import-readback/RectangularBare.SLDPRT",
             "302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357"),
    "literal": (None, "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23"),
}
LITERAL = ("601289d81cfdf429a0be0ea6f4ee84545122c2a9:"
           "re/solidworks/v2026/corpus/part-properties/CircularProperties.SLDPRT")
LANE = "Contents/Config-0"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(data):
    return sha256(data).hexdigest()


@contextmanager
def guard_runtime():
    active = True
    events = []

    def audit(event, _args):
        if active and (event in {"open", "os.listdir", "os.scandir", "ctypes.dlopen", "subprocess.Popen",
                                 "os.system", "os.exec", "os.fork", "os.forkpty", "os.posix_spawn"}
                       or event.startswith("socket.")):
            events.append(event)
            raise PermissionError("configuration codec attempted " + event)

    sys.addaudithook(audit)
    try:
        yield events
    finally:
        active = False


def open_case(case):
    path, expected = CASES[case]
    data = path.read_bytes() if path is not None else check_output(("git", "-C", str(ROOT), "show", LITERAL))
    require(identity(data) == expected, "exact disclosed input identity differs")
    return data, expected


def read_scope(archive):
    references = []

    def inspect(frame, event, _argument):
        if event == "call" and frame.f_code is ReadFrameOwnMut.__code__:
            state = frame.f_locals["FrameValue"]
            cursor = state.ReaderValue.Cursor
            value, end = ReadTag(cursor.BytesValue, cursor.OffsetValue)
            if state.NodeValue.ClassValue.NameValue == "moUnitComponent_c":
                references.append((cursor.OffsetValue, end, value.IndexValue, state.NodeValue))

    old = sys.getprofile()
    sys.setprofile(inspect)
    try:
        part = ReadPartConfig(archive)
    finally:
        sys.setprofile(old)
    (reference,) = references
    first, end, slot, unit = reference
    require(slot == 2 and unit.FieldsValue["owner"] is part.RootValue, "unit component did not retain the same physical part")
    return part, (first, end, slot, unit)


def check_owners(graph, other):
    rows = {row.IndexValue: row.EntryValue for row in graph.MapValue.EntriesValue}
    peer = {row.IndexValue: row.EntryValue for row in other.MapValue.EntriesValue}
    require(graph.MapBase == other.MapBase == 4 and graph.MapValue.CounterValue == other.MapValue.CounterValue,
            "full read/write changed the inherited map")
    require(rows.keys() == peer.keys() == set(range(1, graph.MapValue.CounterValue))
            and all(peer[index] is value if isinstance(value, ArchiveNode) else peer[index] == value
                    for index, value in rows.items()), "complete emission changed the physical map slots")
    require(rows[2] is graph.RootValue and rows[3] is graph.HeaderValue.FieldsValue["f38"],
            "configuration map no longer uses the actual root and original header object")
    return sum(type(value) is RuntimeClass for value in rows.values())


def rejection(call, expected):
    try:
        call()
    except ValueError as error:
        require(expected in str(error), "unexpected refusal: " + str(error))
        return str(error)
    raise ValueError("malformed ordinary configuration was admitted")


def check_faults(raw, graph, reference):
    offset, end, _slot, unit = reference
    wrong_tag = EncodeTag(ArchiveTag("ObjectRef", 3))
    require(end - offset == len(wrong_tag), "control must keep the original owner field width")
    bad_owner = raw[:offset] + wrong_tag + raw[end:]
    rows = {}
    for name, data, diagnostic in (
        ("one_byte", raw[:1], "no complete unsigned short"),
        ("truncated_resolved", raw[:-1], "section exceeds its remaining stream"),
        ("trailing_bytes", raw + b"\x00", "1 trailing bytes"),
        ("wrong_unit_owner", bad_owner, "component owner differs from its enclosing part"),
    ):
        rows[name] = rejection(lambda: ReadConfigMut(data, 19000, graph.HeaderValue), diagnostic)
    saved = unit.FieldsValue["owner"]
    try:
        unit.FieldsValue["owner"] = graph.HeaderValue.FieldsValue["f38"]
        rows["wrong_writer_owner"] = rejection(
            lambda: WriteConfigMut(graph.RootValue, 19000, graph.HeaderValue),
            "component owner differs from its enclosing part",
        )
    finally:
        unit.FieldsValue["owner"] = saved
    return rows


def measure(case):
    blob, pin = open_case(case)
    for name in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(name)
    with guard_runtime() as accesses:
        archive = SldprtArchive.from_bytes(blob)
        config = archive.require(LANE)
        prefix = ReadPartStart(archive)
        graph, reference = read_scope(archive)
        emitted, write_graph = WriteConfigMut(graph.RootValue, 19000, graph.HeaderValue)
        classes = check_owners(graph, write_graph)
        require(config == emitted and graph.RootValue.EndOffset == len(config)
                and graph.ReportValue["completed"] and write_graph.ReportValue["completed"]
                and graph.ReportValue["used_schemas"] == write_graph.ReportValue["used_schemas"],
                "complete part configuration did not re-emit with the same extent and grammar")
        end = prefix.LightOffset + prefix.LightSize
        resolved_size = unpack_from("<I", config, end)[0]
        require(end + 4 + resolved_size == len(config), "independent native section extents differ")
        refusals = check_faults(config, graph, reference)
    require(not accesses, "read/write proof attempted external access")
    return {"case": case, "source_sha256": pin, "config_sha256": identity(config),
            "exact_replay": True, "runtime_external_accesses": len(accesses),
            "bytes": len(emitted), "map_base": graph.MapBase, "map_counter": graph.MapValue.CounterValue,
            "runtime_classes": classes, "schema_count": len(graph.ReportValue["used_schemas"]),
            "lightweight": [prefix.LightOffset, end], "resolved": [end + 4, len(config)],
            "unit_owner": list(reference[:3]), "all_map_slots_preserved": True,
            "refusals": refusals}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("case", choices=tuple(CASES))
    print(json.dumps(measure(parser.parse_args().case), sort_keys=True, allow_nan=False))
