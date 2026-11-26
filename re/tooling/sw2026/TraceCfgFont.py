from codecs import lookup
from collections import Counter
from hashlib import sha256
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from io import BytesIO
import json
from pathlib import Path
from subprocess import check_output
import sys
from tarfile import open as open_tar

ROOT = Path(__file__).resolve().parents[3]
REVISION = "9f0ccb5389c121e750ca3b73f8e5d248b34d2e15"
CASES = {
    "ladder": (
        "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
    ),
    "concave": (
        "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
    ),
}
LAYOUTS = {
    "uiLFConfig_c",
    "utLineWidth_c.Serialize.2.0",
    "utCharFormat_c",
    "utLineWidthPrintData_c",
}
ARCHIVE = "convert.adapters.solidworks.Archive."
LABEL_WIDTH = "utLineWidth_c.Serialize0"


class PinnedSdk(MetaPathFinder, Loader):
    def __init__(self, source=None):
        self.modules = {}
        self.packages = set()
        if source is None:
            source = check_output(("git", "archive", REVISION, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(source), mode="r:") as archive:
            for entry in archive:
                path = entry.name.removeprefix("src/")
                if entry.isdir():
                    self.packages.add(path.replace("/", "."))
                elif entry.isfile() and path.endswith(".py"):
                    name = path.removesuffix(".py").removesuffix("/__init__").replace("/", ".")
                    self.modules[name] = (entry.name, archive.extractfile(entry).read())

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.modules:
            return ModuleSpec(fullname, self, is_package=fullname in self.packages)
        if fullname in self.packages:
            return ModuleSpec(fullname, None, is_package=True)
        return None

    def create_module(self, _spec):
        return None

    def exec_module(self, module):
        name = module.__name__
        path, data = self.modules[name]
        module.__file__ = path
        if name not in ("convert", "convert.adapters.solidworks"):
            exec(compile(data, path, "exec"), module.__dict__)


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_run(event, _args):
    if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec",
                 "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen") or event.startswith("socket."):
        raise PermissionError("the pinned archive trace attempted external access")


def descriptor(node):
    return [node.ClassValue.NameValue, node.ClassValue.SchemaValue, node.IndexValue]


def record_positions(run, body, control, version, config, header):
    counts, rows = Counter(), {}
    label_width = {}
    read_schema = body.ReadSchemaMut

    def observe(frame, layout):
        usage = frame.ContextValue.UsageValue
        if layout == LABEL_WIDTH and "moDrViewLabelData_c" in usage.SchemaPath and not label_width:
            cursor = frame.ReaderValue.Cursor
            start = cursor.GetOffset()
            read_schema(frame, layout)
            end = cursor.GetOffset()
            label_width.update(interval=[start, end], owner_fields=list(usage.FieldPath),
                               wire_sha256=digest(config[start:end]))
            return None
        if layout not in LAYOUTS:
            return read_schema(frame, layout)
        counts[layout] += 1
        if layout in rows or (layout == "utCharFormat_c" and "moDrViewLabelData_c" not in usage.SchemaPath):
            return read_schema(frame, layout)
        reader = frame.ReaderValue
        start, before = reader.Cursor.GetOffset(), reader.MapValue.Snapshot()
        scope, lane = list(usage.SchemaPath), list(usage.FieldPath)
        base = reader.MapValue.BaseValue
        read_schema(frame, layout)
        end, after = reader.Cursor.GetOffset(), reader.MapValue.Snapshot()
        require(base == reader.MapValue.BaseValue == 4 and before.CounterValue == after.CounterValue
                and len(before.EntriesValue) == len(after.EntriesValue)
                and all(left is right for left, right in zip(before.EntriesValue, after.EntriesValue, strict=True)),
                "the pinned formatting record changed the native map")
        root, alias = after.EntriesValue[1:3]
        require(root.IndexValue == 2 and root.EntryValue is frame.NodeValue and alias.IndexValue == 3,
                "the traced fields are not members of the mapped part")
        require([entry.IndexValue for entry in before.EntriesValue] == list(range(1, before.CounterValue)),
                "the pinned incoming map has a different slot order")
        rows[layout] = {
            "layout": layout, "scope": scope, "owner_fields": lane,
            "interval": [start, end], "wire_sha256": digest(config[start:end]),
            "map_base": base, "map_counter": before.CounterValue,
            "native_map_slot_range": [1, before.CounterValue],
            "part": descriptor(frame.NodeValue),
            "header_alias": descriptor(alias.EntryValue),
            "conditions": frame.ContextValue.FlagsValue.get("conditions", 0),
        }
        return None

    body.ReadSchemaMut = observe
    try:
        result = run(config, version, header)
    finally:
        body.ReadSchemaMut = read_schema
    require(set(rows) == LAYOUTS and label_width and result.RootValue is not None,
            f"{control} did not traverse all four typed owners")
    return {"layout_calls": dict(counts), "records": rows,
            "next_label_width": label_width,
            "complete_pinned_graph": result.ReportValue["completed"],
            "pinned_config_counter": result.MapValue.CounterValue}


def main():
    pin = PinnedSdk()
    sys.meta_path.insert(0, pin)
    config_reader = import_module(ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
    header_reader = import_module(ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
    body = import_module(ARCHIVE + "Bodies.ReadBodyMut")
    container = import_module("convert.adapters.solidworks.Container.Container").SldprtArchive
    version_of = import_module("convert.adapters.solidworks.Container.Archive").ContainerMo
    sources = {name: (path, expected, (ROOT / path).read_bytes())
               for name, (path, expected) in CASES.items()}
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    controls = {}
    for name, (path, expected, source) in sources.items():
        require(digest(source) == expected, "wrong tracked native part")
        arc = container.from_bytes(source)
        version = version_of(arc.streams)
        require(arc.format_version == 4 and version == 19000, "wrong physical native profile")
        config = arc.require("Contents/Config-0")
        header_bytes = arc.require("Contents/Config-0-ModelHeader")
        header = header_reader(header_bytes, version)
        result = record_positions(config_reader, body, name, version, config, header)
        result.update(path=path, source_sha256=expected, config_sha256=digest(config),
                      model_header_sha256=digest(header_bytes))
        controls[name] = result
    print(json.dumps({
        "format_version": 4, "archive_version": 19000, "pinned_archive_reader": REVISION,
        "stream": "Contents/Config-0", "model_header": "Contents/Config-0-ModelHeader",
        "native_controls": controls, "runtime_external_accesses": 0,
    }, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
