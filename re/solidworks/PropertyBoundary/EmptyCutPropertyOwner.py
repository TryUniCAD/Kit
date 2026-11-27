from argparse import ArgumentParser
from codecs import lookup
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "re/automation"), str(ROOT / "re/solidworks/EncoderBoundary")]

from EncoderRoundTrip.Artifacts import canonical_json, digest, read_record, write_artifact
from InspectVendorBodyOwners import REVISION, verify_dependency

SCHEMA = "kit.research.empty-cut-property-owner.v1"
XML_FILES = {"docProps/core.xml": "Core.xml", "docProps/custom.xml": "Custom.xml", "docProps/Config-0-Properties.xml": "Configuration.xml"}


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def read_request(raw):
    value = read_record(raw)
    demand(set(value) == {"schema", "empty_cut_owner"} and value["schema"] == SCHEMA, "expected only explicit empty cut-owner intent")
    demand(type(value["empty_cut_owner"]) is bool, "empty cut-owner presence must be a Boolean")
    demand(raw == canonical_json(value), "property request must use canonical JSON")
    return value["empty_cut_owner"]


def make_owner(present):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

    demand(type(present) is bool, "empty cut-owner presence must be a Boolean")
    file = ArchiveNode(RuntimeClass("moFilePropContainer_c", 1), {"f08": None, "f10": None})
    cut = ArchiveNode(RuntimeClass("moCutListPropContainer_c", 1), {"f08": (), "f38": ()}) if present else None
    container = ArchiveNode(RuntimeClass("moCusPropContainer_c", 1), {"f08": file, "f10": cut, "f18": None, "f20": 0})
    return ArchiveNode(RuntimeClass("moCusPropMgr_c", 1), {"f0c": -1, "f08": 1, "f20": ({"key": 0, "o": container},), "f54": 0})


def emit(root):
    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Properties.CheckEmptyProps import CheckEmptyProps
    from convert.adapters.solidworks.Archive.Properties.MakePropContext import MakePropContext

    CheckEmptyProps(root)
    writer = BodyWriter(ArchiveMaps(1), MakePropContext(19000), WriteBodyMut)
    WriteNodeMut(writer, root)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def require_node(value, name, fields):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

    demand(isinstance(value, ArchiveNode) and value.ClassValue == RuntimeClass(name, 1)
           and set(value.FieldsValue) == fields, "property owner class or complete fields differ")
    return value.FieldsValue


def inspect(data, present):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropManager, ReadPropRoot

    ReadPropManager(data, 19000)
    root = ReadPropRoot(data, 19000)
    fields = require_node(root, "moCusPropMgr_c", {"f0c", "f08", "n20", "f20", "f54"})
    demand((fields["f0c"], fields["f08"], fields["n20"], fields["f54"]) == (-1, 1, 1, 0), "property scope requires its concrete key-zero owner")
    row, = fields["f20"]
    demand(set(row) == {"key", "o"} and row["key"] == 0, "property container must belong to key zero")
    container = row["o"]
    scope = require_node(container, "moCusPropContainer_c", {"f08", "f10", "f18", "f20"})
    file = scope["f08"]
    demand(require_node(file, "moFilePropContainer_c", {"f08", "f10"}) == {"f08": None, "f10": None}
           and scope["f18"] is None and scope["f20"] == 0, "property file or extra scopes are not empty")
    nodes = [root, container, file]
    cut = scope["f10"]
    demand((cut is not None) == present, "actual cut-owner presence differs from the request")
    if present:
        values = require_node(cut, "moCutListPropContainer_c", {"n08", "f08", "n38", "f38"})
        demand(values["n08"] == values["n38"] == 0 and not values["f08"] and not values["f38"], "cut owner contains property rows")
        nodes.append(cut)
    demand(len({id(node) for node in nodes}) == len(nodes), "property owners alias unexpectedly")
    repeated, snapshot = emit(root)
    demand(repeated == data, "property owner graph does not re-emit exactly")
    actual = sorted((node.IndexValue, node.ClassValue.NameValue) for node in nodes)
    stored = [(entry.IndexValue, entry.EntryValue.ClassValue.NameValue) for entry in snapshot.EntriesValue if isinstance(entry.EntryValue, ArchiveNode)]
    demand(actual == stored, "property read/write object map differs")
    return {"actual_cut_owner": cut is not None, "key": row["key"], "file_lists_null": True, "cut_lists_empty": True if present else None,
            "owner_slots": actual, "map_next": snapshot.CounterValue, "exact_reemit": True, "exact_object_map": True}


def manufacture(present):
    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import MakePartProps
    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput

    root = make_owner(present)
    data, _ = emit(root)
    xml = MakePartProps(PartTextInput({}, {}, {}, frozenset(("summary", "document", "configuration"))))
    return data, xml, inspect(data, present)


def initialize(root):
    verify_dependency(root)
    from convert.adapters.solidworks.Archive.Properties import ReadPropManager
    from convert.adapters.solidworks.Archive.Properties import MakePropContext
    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import MakePartProps
    from convert.adapters.solidworks.Archive.Bodies import BodyWriter, WriteBodyMut
    from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
    from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps

    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)


def check_xml(xml):
    from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
    from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps

    demand(set(xml) == set(XML_FILES), "expected all three empty XML scopes")
    for name, data in xml.items():
        values = ReadCoreProps(data) if name == "docProps/core.xml" else ReadCustomProps(data, name.startswith("docProps/Config-"))
        demand(values == {}, "property XML contains authored text")


def generate(args):
    initialize(args.dependency_root)
    raw = args.request.read_bytes()
    present = read_request(raw)
    active, attempts = True, []

    def audit(event, _):
        if active and (event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.spawn", "os.startfile", "os.posix_spawn", "os.fork", "os.forkpty")
                       or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise RuntimeError("external input during empty-owner manufacture")

    sys.addaudithook(audit)
    try:
        data, xml, fields = manufacture(present)
    finally:
        active = False
    demand(not attempts, "property construction crossed its offline boundary")
    check_xml(xml)
    demand(args.request.read_bytes() == raw, "property request changed during generation")
    verify_dependency(args.dependency_root)
    args.output.mkdir()
    retained = {"Contents/CusProps": write_artifact(args.output, "Properties.bin", data)}
    retained.update({name: write_artifact(args.output, XML_FILES[name], payload) for name, payload in xml.items()})
    write_artifact(args.output, "Request.json", raw)
    report = {"schema": SCHEMA, "stage": "source_free_property_substream", "request_sha256": digest(raw), "method_sha256": digest(Path(__file__).read_bytes()),
              "dependency": REVISION, "empty_cut_owner": present, "fields": fields, "streams": retained, "external_manufacture_attempts": 0, "native_launches": 0}
    write_artifact(args.output, "Evidence.json", canonical_json(report))
    return report


def read_source(args):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropRoot

    original = args.source.read_bytes()
    demand(digest(original) == args.source_sha, "source differs from its pinned digest")
    archive = SldprtArchive.from_bytes(original, "<property owner comparator>")
    demand(ContainerMo(archive.streams) == 19000, "source requires the measured version19000 archive")
    native = archive.Require("Contents/CusProps")
    source_root = ReadPropRoot(native, 19000)
    demand(len(source_root.FieldsValue["f20"]) == 1, "source comparison requires the actual keyed file owner")
    present = source_root.FieldsValue["f20"][0]["o"].FieldsValue["f10"] is not None
    fields = inspect(native, present)
    xml = {name: archive.Require(name) for name in XML_FILES}
    check_xml(xml)
    demand(digest(args.source.read_bytes()) == args.source_sha, "source changed during comparison")
    return native, fields, xml


def extract(args):
    initialize(args.dependency_root)
    native, fields, xml = read_source(args)
    request = canonical_json({"schema": SCHEMA, "empty_cut_owner": fields["actual_cut_owner"]})
    verify_dependency(args.dependency_root)
    args.output.mkdir()
    write_artifact(args.output, "Request.json", request)
    report = {"schema": SCHEMA, "stage": "source_bound_empty_property_projection", "source_sha256": args.source_sha,
              "method_sha256": digest(Path(__file__).read_bytes()), "dependency": REVISION, "request_sha256": digest(request),
              "source_property_sha256": digest(native), "fields": fields,
              "source_empty_xml_sha256": {name: digest(data) for name, data in xml.items()}, "native_launches": 0}
    write_artifact(args.output, "SourceEvidence.json", canonical_json(report))
    return report


def compare(args):
    initialize(args.dependency_root)

    evidence = read_record((args.generated / "Evidence.json").read_bytes())
    request = (args.generated / "Request.json").read_bytes()
    present = read_request(request)
    demand(evidence["schema"] == SCHEMA and evidence["stage"] == "source_free_property_substream"
           and evidence["external_manufacture_attempts"] == evidence["native_launches"] == 0
           and evidence["empty_cut_owner"] is present and evidence["request_sha256"] == digest(request) and evidence["dependency"] == REVISION
           and evidence["method_sha256"] == digest(Path(__file__).read_bytes()), "generated custody or method differs")
    values = {}
    for name, entry in evidence["streams"].items():
        demand(Path(entry["path"]).name == entry["path"], "generated member name escapes its directory")
        data = (args.generated / entry["path"]).read_bytes()
        demand(entry == {"path": entry["path"], "bytes": len(data), "sha256": digest(data)}, "generated member custody differs")
        values[name] = data
    demand(set(values) == {"Contents/CusProps", *XML_FILES}, "generated property scope differs")
    fields = inspect(values["Contents/CusProps"], present)
    demand(canonical_json(fields) == canonical_json(evidence["fields"]), "generated owner receipt differs from actual readback")
    check_xml({name: values[name] for name in XML_FILES})
    native, source_fields, source_xml = read_source(args)
    verify_dependency(args.dependency_root)
    report = {"schema": SCHEMA, "stage": "optional_post_generation_comparison", "source_sha256": args.source_sha,
              "generated_request_sha256": digest(request), "generated_fields": fields, "source_fields": source_fields,
              "source_property_sha256": digest(native), "property_bytes_equal": native == values["Contents/CusProps"],
              "xml_byte_equal": {name: source_xml[name] == values[name] for name in XML_FILES}, "native_launches": 0}
    args.output.mkdir()
    write_artifact(args.output, "Comparison.json", canonical_json(report))
    return report


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate only a typed empty property substream and empty XML scopes")
    commands = parser.add_subparsers(dest="command", required=True)
    writer = commands.add_parser("generate")
    writer.add_argument("--request", type=Path, required=True)
    reader = commands.add_parser("compare")
    reader.add_argument("--generated", type=Path, required=True)
    producer = commands.add_parser("extract")
    for command in (reader, producer):
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--source-sha", required=True)
    for command in (writer, reader, producer):
        command.add_argument("--dependency-root", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    action = {"generate": generate, "compare": compare, "extract": extract}[args.command]
    sys.stdout.buffer.write(canonical_json(action(args)))
