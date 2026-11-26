from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from
from uuid import UUID

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigSavedViews import WriteSavedViews
from ConfigScene.Annotation import KAnnotation, WriteAnnotViews
from ConfigScene.ModelLists import PartMarker, WriteModelLists
from ConfigScene.SketchBlock import WriteSketchBlock
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import (
    ReadModelTagMut,
    ReadSavedAnnots,
)
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
    KDefinitionKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the real archive walk identifies the list at the allocation before its first view
def inspect_annos(
    config: bytes, generation: int, name: str, include_top: bool
) -> tuple[int, str]:
    final, walk = ReadOrdinaryMap(config, generation)
    events = walk["pointers"]
    (index,) = (
        i
        for i, event in enumerate(events)
        if event[2:4] == (KDefinitionKind, KAnnotation)
    )
    require(index > 0, "annotation list precedes the first view")
    start, count, kind, owner, _ = events[index - 1]
    require((kind, owner) == (KClassRefKind, "suObList"), "typed annotation list")
    inherited = PartArchiveState(
        count,
        tuple(sorted((i, n) for i, n in final.Classes.items() if i < count)),
        tuple(sorted((i, n) for i, n in final.Objects.items() if i < count)),
    )
    native = inherited.Cursor(config, start)
    read_native = partial(ReadModelTagMut, native, [])
    ReadSavedAnnots(native, read_native)
    stop = native.Offset
    after = allocation_state(native)
    require(
        after.NextIndex == count + 3 + int(include_top), "annotation allocation count"
    )
    ReadModelLists(native, read_native)

    writer = PartArchiveWriter(inherited)
    WriteAnnotViews(writer, generation, name, include_top)
    encoded = writer.build()
    require(encoded == config[start:stop], "exact constructed annotation views")
    reread = inherited.Cursor(encoded + config[stop : native.Offset], 0)
    read_back = partial(ReadModelTagMut, reread, [])
    ReadSavedAnnots(reread, read_back)
    require(
        reread.Offset == len(encoded)
        and writer.Snapshot() == allocation_state(reread) == after,
        "constructed annotation view extent and full map",
    )
    ReadModelLists(reread, read_back)
    require(
        reread.Offset == native.Offset - start
        and allocation_state(reread) == allocation_state(native),
        "independent following model lists consume the same archive span and map",
    )
    return len(encoded), sha256(encoded).hexdigest()


def report() -> dict[str, object]:
    captures: dict[str, str] = {}
    spans: dict[int, int] = {}
    for recipe, asset, data, _, measurement in principal_captures():
        (normal,) = (
            tuple(sketch["model_to_sketch_transform"][6:9])
            for sketch in measurement["sketches"]
            if sketch["name"] == "RectangleSketch"
        )
        require(normal in ((0, 0, 1), (-1, 0, 0)), "measured principal sketch pose")
        name = "*Front" if normal == (0, 0, 1) else "*Right"
        archive = SldprtArchive.from_bytes(data, asset["path"])
        generation = ContainerMo(archive.streams)
        require(generation == 19000, "modern annotation configuration")
        width, digest = inspect_annos(
            archive.require("Contents/Config-0"), 19000, name, recipe == "P03"
        )
        spans[width] = spans.get(width, 0) + 1
        captures[asset["sha256"]] = digest
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "span_counts": spans,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }


def graph_allocation(graph: ConfigGraph, counter: int) -> PartArchiveState:
    entries = sorted(graph.MapValue.EntriesValue, key=lambda entry: entry.IndexValue)
    prefix = [
        (entry.IndexValue, entry.EntryValue)
        for entry in entries
        if entry.IndexValue < counter
    ]
    return PartArchiveState(
        counter,
        tuple(
            (index, obj.NameValue)
            for index, obj in prefix
            if isinstance(obj, RuntimeClass)
        ),
        tuple(
            (index, obj.ClassValue.NameValue)
            for index, obj in prefix
            if isinstance(obj, ArchiveNode)
        ),
    )


def top_native(path: Path) -> tuple[str, dict[str, object]]:
    data = path.read_bytes()
    archive = SldprtArchive.from_bytes(data, str(path))
    config = archive.Require("Contents/Config-0")
    graph = ReadPartConfig(archive)
    root = graph.RootValue.FieldsValue
    owner = root["fa48"]
    require(
        isinstance(owner, ArchiveNode) and owner.ClassValue == RuntimeClass("suObList", 1),
        "part annotation list owner",
    )
    require(owner.FieldsValue["n"] == 1, "part owns a single annotation view")
    (item,) = owner.FieldsValue["items"]
    view = item["o"]
    require(
        isinstance(view, ArchiveNode)
        and view.ClassValue == RuntimeClass(KAnnotation, 1)
        and view.IndexValue == owner.IndexValue + 2
        and view.FieldsValue["f358"] == "*Top"
        and view.FieldsValue["f360"] == 200
        and view.EndOffset == owner.EndOffset,
        "part owner has one first-ID Top annotation",
    )
    start, stop = owner.StartOffset, owner.EndOffset
    inherited = graph_allocation(graph, owner.IndexValue)
    after = graph_allocation(graph, view.IndexValue + 1)
    thread = root["f12d0"]
    require(thread.ClassValue == RuntimeClass("moCThreadRefMgr_c", 1), "following thread manager")
    following = graph_allocation(graph, thread.IndexValue + 1)
    following_stop = thread.EndOffset + ReadTag(config, thread.EndOffset).size
    native = inherited.Cursor(config, start)
    read_native = partial(ReadModelTagMut, native, [])
    ReadSavedAnnots(native, read_native, Scoped=True)
    require(
        native.Offset == stop and allocation_state(native) == after,
        "native annotation extent and map",
    )
    require(unpack_from("<i", config, stop) == (200,), "native annotation display high-water ID")
    ReadModelLists(native, read_native)
    require(
        native.Offset == following_stop and allocation_state(native) == following,
        "native following list extent and map",
    )

    writer = PartArchiveWriter(inherited)
    WriteAnnotViews(writer, graph.VersionValue, "*Top", False)
    encoded = writer.build()
    require(
        encoded == config[start:stop] and writer.Snapshot() == after,
        "exact Top-only reconstruction",
    )
    reread = inherited.Cursor(encoded + config[stop:following_stop], 0)
    read_back = partial(ReadModelTagMut, reread, [])
    ReadSavedAnnots(reread, read_back, Scoped=True)
    require(
        reread.Offset == len(encoded) and allocation_state(reread) == after,
        "constructed Top-only extent and map",
    )
    ReadModelLists(reread, read_back)
    require(
        reread.Offset == following_stop - start and allocation_state(reread) == following,
        "following list consumes the original extent and map",
    )
    matrix = view.FieldsValue["f368"]["f08"]
    return sha256(data).hexdigest(), {
        "annotation": {"name": "*Top", "id": 200, "schema": view.ClassValue.SchemaValue},
        "annotation_matrix": [matrix[f"m{index}"].hex() for index in range(9)],
        "annotation_owner": "moPart_c.fa48",
        "config_sha256": sha256(config).hexdigest(),
        "display_high_water": 200,
        "following_offset": following_stop,
        "list_slot": owner.IndexValue,
        "list_span": [start, stop],
        "list_sha256": sha256(encoded).hexdigest(),
        "next_slots": [after.NextIndex, following.NextIndex],
        "object_slot": view.IndexValue,
        "object_span": [view.StartOffset, view.EndOffset],
    }


def top_synthesized() -> dict[str, object]:
    prefix = PartArchiveWriter()
    WriteSavedViews(prefix, 19000)
    WriteSketchBlock(prefix, 19000, Stamp(0, 0), UUID(int=1))
    inherited = prefix.Snapshot()
    writer = PartArchiveWriter(inherited)
    try:
        WriteAnnotViews(writer, 19000, "*Top", True)
    except ArchiveError:
        require(
            writer.Snapshot() == inherited and not writer.build(),
            "duplicate Top refusal preserves allocator",
        )
    else:
        raise ValueError("duplicate Top must refuse")
    WriteAnnotViews(writer, 19000, "*Top", False)
    annotation = writer.build()
    after = writer.Snapshot()
    WriteModelLists(writer, 19000, PartMarker(3, 1))
    generated = writer.build()
    require(
        unpack_from("<i", generated, len(annotation)) == (200,),
        "generated annotation display high-water ID",
    )
    cursor = inherited.Cursor(generated, 0)
    take = partial(ReadModelTagMut, cursor, [])
    ReadSavedAnnots(cursor, take, Scoped=True)
    require(
        cursor.Offset == len(annotation) and allocation_state(cursor) == after,
        "generated Top-only extent and map",
    )
    ReadModelLists(cursor, take)
    require(
        cursor.Offset == len(generated) and allocation_state(cursor) == writer.Snapshot(),
        "generated following model lists",
    )
    return {
        "list_bytes": len(annotation),
        "list_sha256": sha256(annotation).hexdigest(),
        "following_bytes": len(generated) - len(annotation),
        "duplicate_top_refused": True,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify generation-19000 annotation views")
    parser.add_argument(
        "--top-only",
        nargs="*",
        type=Path,
        help="generate a Top-only list and optionally compare independent native saves",
    )
    top_paths = parser.parse_args().top_only
    if top_paths is None:
        result = report()
    else:
        result = {"synthetic": top_synthesized(), "native": dict(map(top_native, top_paths))}
    print(json.dumps(result, sort_keys=True))
