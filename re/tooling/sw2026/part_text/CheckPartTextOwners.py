from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

from CheckOrdinaryCfg import LANE, guard_runtime
from CheckPhysicalPartText import CONFIG_SHA, CONFIG_TEXT, SOURCE_SHA, exercise
from PartTextProbe import check_model, model_state, read_part
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import KSketchBlockClass
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

HEADER = "Contents/Config-0-ModelHeader"
HEADER_CAUSE = "part configuration properties differ from the saved ModelHeader name"
BLOCK_CAUSE = "SOLIDWORKS sketch block map requires its owning backlink"


def header_case(archive):
    original = archive.require(HEADER)
    graph = ReadModelHead(archive, 19000)
    owner = graph.FieldsValue["f38"]
    entry = GetFileRef(owner)
    if entry.ConfigValue != "modeled default" or WriteHeadGraph(graph, 19000) != original:
        raise ValueError("the original ModelHeader identity and wire replay must be exact")
    config = owner.FieldsValue["refcfg"]
    config["f08"] = replace(config["f08"], TextValue="shifted default")
    wire = WriteHeadGraph(graph, 19000)
    seen = GetFileRef(ReadHeaderGraph(wire, 19000).FieldsValue["f38"])
    if seen != replace(entry, ConfigValue="shifted default") or len(wire) != len(original):
        raise ValueError("the name contrast changed the header shape or file identity")
    return wire, [entry.ConfigValue, seen.ConfigValue]


def block_case(archive):
    spans = []

    def inspect(frame, event, _argument):
        if event != "call" or frame.f_code is not ReadValueMut.__code__:
            return
        rule = frame.f_locals["RuleValue"]
        state = frame.f_locals["FrameValue"]
        if rule.NameValue == "f30" and state.NodeValue.ClassValue == KSketchBlockClass:
            cursor = state.ReaderValue.Cursor
            value, end = ReadTag(cursor.BytesValue, cursor.OffsetValue)
            spans.append((cursor.OffsetValue, end, value, state.NodeValue))

    prior = sys.getprofile()
    sys.setprofile(inspect)
    try:
        graph = ReadPartConfig(archive)
    finally:
        sys.setprofile(prior)
    (start, stop, tag, block), = spans
    root_slot = graph.RootValue.IndexValue
    initial_slot = block.IndexValue
    entries = {row.IndexValue: row.EntryValue for row in graph.MapValue.EntriesValue}
    if (tag != ArchiveTag("ObjectRef", initial_slot) or root_slot == initial_slot
            or entries[root_slot] is not graph.RootValue or entries[initial_slot] is not block
            or block.FieldsValue["blocks"]["f30"] is not block):
        raise ValueError("the sketch block map control no longer proves its self backlink")
    pointer = EncodeTag(ArchiveTag("ObjectRef", root_slot))
    raw = archive.require(LANE)
    if stop - start != len(pointer) or raw[start:stop] != EncodeTag(tag):
        raise ValueError("the substituted part link must preserve the native tag shape")
    return raw[:start] + pointer + raw[stop:], [start, stop, initial_slot, root_slot]


def prepare(path):
    native = path.read_bytes()
    archive = SldprtArchive.from_bytes(native)
    if (sha256(native).hexdigest(), sha256(archive.require(LANE)).hexdigest()) != (SOURCE_SHA, CONFIG_SHA):
        raise ValueError("the disclosed literal control changed")
    for name in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(name)
    with guard_runtime() as events:
        header, names = header_case(archive)
        block, link = block_case(archive)
        streams = {**archive.streams, HEADER: header}
        moved_header = SldprtArchive.from_bytes(BuildSldprt(streams, FormatVersion=archive.format_version))
        if moved_header.streams != streams:
            raise ValueError("the header contrast changed another physical stream")
    return native, archive, moved_header, block, names, link, events


def measure(path):
    native, archive, header, block, names, link, events = prepare(path)
    doc = read_part(native)
    baseline = model_state(doc)
    if baseline["status"]["status"] != "complete" or not all(baseline["text_scopes"]):
        raise ValueError("the unmodified control must recover all authored text scopes")
    rows = {
        "wrong_header_name": exercise(
            header, doc, baseline, archive.require(LANE), HEADER_CAUSE, (), config_rejected=False,
        ),
        "wrong_block_owner": exercise(
            archive, doc, baseline, block, BLOCK_CAUSE, (), config_rejected=True,
        ),
    }
    unscoped = {key: value for key, value in header.streams.items() if key != CONFIG_TEXT}
    independent = read_part(BuildSldprt(unscoped, FormatVersion=archive.format_version))
    check_model(doc, independent)
    state = model_state(independent)
    if (state["text_scopes"] != [True, True, False] or state["status"]["status"] != "complete"
            or independent.metadata["document_summary"] != doc.metadata["document_summary"]
            or independent.metadata["custom_properties"] != doc.metadata["custom_properties"]):
        raise ValueError("independent file-level text now depends on a configuration label")
    if events or path.read_bytes() != native:
        raise ValueError("guarded owner inspection modified or accessed external data")
    return {
        "schema": "kit.sw2026.literal-part-text-owners.v2",
        "source_sha256": SOURCE_SHA,
        "positive_config": CONFIG_SHA,
        "original_header": sha256(archive.require(HEADER)).hexdigest(),
        "contrasted_header": sha256(header.require(HEADER)).hexdigest(),
        "contrasted_config": sha256(block).hexdigest(),
        "native_header_names": names,
        "native_block_link": link,
        "typed_external_accesses": len(events),
        "cases": rows,
        "unscoped_text": state["text_scopes"],
    }


if __name__ == "__main__":
    print(json.dumps(measure(Path(sys.argv[1])), sort_keys=True, allow_nan=False))
