from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

from PartTextProbe import (
    PROPERTY_DIAGNOSTIC,
    check_model,
    model_state,
    read_part,
    refuse_write,
)
from CheckOrdinaryCfg import LANE, guard_runtime, read_scope
from convert import convert, write_document
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

SOURCE_SHA = "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23"
CONFIG_SHA = "5c78942508f55177db00ea7f394856a6d8c72683b19163b4e3d14e557fe045c7"
CONFIG_TEXT = "docProps/Config-0-Properties.xml"
DOCUMENT_TEXT = "docProps/custom.xml"


def variants(archive):
    config = archive.require(LANE)
    graph, (start, end, slot, unit) = read_scope(archive)
    alias = graph.HeaderValue.FieldsValue["f38"]
    (wrong_slot,) = (
        entry.IndexValue
        for entry in graph.MapValue.EntriesValue
        if entry.EntryValue is alias
    )
    tag = EncodeTag(ArchiveTag("ObjectRef", wrong_slot))
    if (slot == wrong_slot or len(tag) != end - start
            or unit.FieldsValue["owner"] is not graph.RootValue):
        raise ValueError("native unit-owner control has changed")
    cases = {
        "one_byte": (config[:1], "no complete unsigned short", ()),
        "tail_truncated": (config[:-1], "section exceeds its remaining stream", ()),
        "appended": (config + b"\x00", "1 trailing bytes", ()),
        "wrong_owner": (
            config[:start] + tag + config[end:],
            "component owner differs from its enclosing part",
            (),
        ),
        "summary_only_truncated": (
            config[:-1], "section exceeds its remaining stream",
            (CONFIG_TEXT, DOCUMENT_TEXT),
        ),
    }
    return cases, [start, end, slot, wrong_slot]


def exercise(archive, original, baseline, config, reason, absent_xml):
    streams = dict(archive.streams)
    streams[LANE] = config
    for name in absent_xml:
        del streams[name]
    data = BuildSldprt(streams, FormatVersion=archive.format_version)
    if SldprtArchive.from_bytes(data).streams != streams:
        raise ValueError("the physical control changed unrelated streams")
    observed = read_part(data)
    check_model(original, observed)
    state = model_state(observed)
    detail = state["status"]
    if (detail["status"] != "unsupported"
            or reason not in detail["diagnostic"]
            or state["diagnostics"] != [(PROPERTY_DIAGNOSTIC, "info", detail["diagnostic"])]
            or any(state["text_scopes"])
            or state["configuration"] != baseline["configuration"]
            or state["body"] != baseline["body"]):
        raise ValueError("physical configuration refusal did not preserve inspection")
    operations = {
        "strict_convert": partial(
            convert, data, source_format="solidworks.sldprt",
            destination_format="interchange.json", strict=True,
            include_tessellation=False,
        ),
        "direct_write": partial(
            write_document, observed, destination_format="interchange.json",
        ),
    }
    state["write_refusals"] = {
        name: refuse_write(call, detail["diagnostic"]) for name, call in operations.items()
    }
    state["config_bytes"] = len(config)
    state["removed_property_xml"] = list(absent_xml)
    state["geometry_equal"] = True
    return state


def inspect(path):
    native = path.read_bytes()
    archive = SldprtArchive.from_bytes(native)
    source_sha = sha256(native).hexdigest()
    config_sha = sha256(archive.require(LANE)).hexdigest()
    if (source_sha, config_sha) != (SOURCE_SHA, CONFIG_SHA):
        raise ValueError("exact disclosed literal configuration changed")
    original = read_part(native)
    baseline = model_state(original)
    if baseline["status"]["status"] != "complete" or not all(baseline["text_scopes"]):
        raise ValueError("intact native circular part did not publish its three scopes")
    with guard_runtime() as events:
        inputs, owner = variants(archive)
    rows = {
        name: exercise(archive, original, baseline, *case)
        for name, case in inputs.items()
    }
    if events or path.read_bytes() != native:
        raise ValueError("typed inspection opened an external source or changed its input")
    if any(name.startswith(("win32com", "pythoncom")) for name in sys.modules):
        raise ValueError("inspection crossed the native runtime boundary")
    return {
        "schema": "kit.sw2026.literal-part-text-physical.v1",
        "source_sha256": source_sha,
        "config_sha256": config_sha,
        "native_unit_owner": owner,
        "original": baseline,
        "cases": rows,
        "typed_external_accesses": len(events),
        "native_processes_started": 0,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True, allow_nan=False))
