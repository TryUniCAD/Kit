from argparse import ArgumentParser
from collections.abc import Mapping
from pathlib import Path
import re
import sys

from ComposeTopAnnotation import (
    ANNOTATION_BASE_ID, ANNOTATION_CLASS, TopAnnotationIntent,
    canonical_json, digest,
)
from ConfigSavedViews import WriteViewBase
from ConfigScene.Annotation import KTop, WriteAnnoTail
from PartArchive import PartArchiveWriter
from VerifyConfigAnnotViews import graph_allocation
from convert import open_document
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartFormatId, KeywordsStream
from convert.adapters.solidworks.Core.Adapter import ConfigId
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.Properties.ReadPropOwners import ReadPropOwners
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.EncodeData import ToData


def bound_configuration(document: CadDocument, archive: SldprtArchive, version: int) -> str:
    names = archive.streams.keys()
    lanes = {
        name for name in names
        if re.fullmatch(r"Contents/Config-\d+(?:-ModelHeader|-ResolvedFeatures)?", name)
    }
    if lanes != {
        "Contents/Config-0", "Contents/Config-0-ModelHeader", "Contents/Config-0-ResolvedFeatures",
    } or any(name.startswith("Kit/") for name in names):
        raise ValueError("Top annotation requires only the physical Config-0 lane without a Kit carrier")
    owners = ReadPropOwners(document, archive, version)
    rows, _ = ParseKeywords(archive.Require(KeywordsStream))
    configuration, = document.configurations
    if (
        tuple(owners) != (0,)
        or configuration.id != ConfigId(0)
        or len(rows) != 1
        or rows[0].configuration_id != 0
        or rows[0].properties.get("id") != "0"
        or rows[0].properties.get("Name") != owners[0]
    ):
        raise ValueError("Top annotation requires matching explicit active configuration identity")
    return configuration.id


def require_exclusive_edges(graph: ConfigGraph, owner: ArchiveNode, view: ArchiveNode) -> None:
    pending = [graph.RootValue, graph.HeaderValue]
    pending.extend(
        entry.EntryValue for entry in graph.MapValue.EntriesValue
        if isinstance(entry.EntryValue, ArchiveNode)
    )
    visited = set()
    found = {owner: [], view: []}
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        fields = [((), node.FieldsValue)]
        while fields:
            path, value = fields.pop()
            if isinstance(value, ArchiveNode):
                pending.append(value)
                if value in found:
                    found[value].append((node, path))
            elif isinstance(value, Mapping):
                fields.extend(((*path, key), child) for key, child in value.items())
            elif isinstance(value, (list, tuple)):
                fields.extend(((*path, index), child) for index, child in enumerate(value))
    if (
        found[owner] != [(graph.RootValue, ("fa48",))]
        or found[view] != [(owner, ("items", 0, "o"))]
    ):
        raise ValueError("Top annotation owner and view must have exclusive typed references")


def checked_view(graph: ConfigGraph, config: bytes) -> ArchiveNode:
    fields = graph.RootValue.FieldsValue
    owner = fields.get("fa48")
    if (
        not isinstance(owner, ArchiveNode)
        or owner.ClassValue != RuntimeClass("suObList", 1)
        or set(owner.FieldsValue) != {"n", "items"}
        or owner.FieldsValue["n"] != 1
        or len(owner.FieldsValue["items"]) != 1
    ):
        raise ValueError("Top annotation requires one direct saved view")
    item, = owner.FieldsValue["items"]
    view = item.get("o")
    if (
        set(item) != {"o"}
        or not isinstance(view, ArchiveNode)
        or view.ClassValue != ANNOTATION_CLASS
        or view.FieldsValue["f358"] != "*Top"
        or view.FieldsValue["f360"] != ANNOTATION_BASE_ID + 1
        or fields["feb0"] != ANNOTATION_BASE_ID + 1
        or fields["feb4"] != ANNOTATION_BASE_ID
    ):
        raise ValueError("Top annotation requires the sole default Top view and its display high-water ID")
    slots = {entry.IndexValue: entry.EntryValue for entry in graph.MapValue.EntriesValue}
    annotation_nodes = [
        entry for entry in slots.values()
        if isinstance(entry, ArchiveNode) and entry.ClassValue == ANNOTATION_CLASS
    ]
    if (
        type(owner.IndexValue) is not int
        or view.IndexValue != owner.IndexValue + 2
        or slots.get(owner.IndexValue) is not owner
        or slots.get(owner.IndexValue + 1) != ANNOTATION_CLASS
        or slots.get(view.IndexValue) is not view
        or annotation_nodes != [view]
        or not 0 <= owner.StartOffset < view.StartOffset < view.EndOffset == owner.EndOffset <= len(config)
    ):
        raise ValueError("Top annotation requires its own tagged object occurrence")
    require_exclusive_edges(graph, owner, view)

    # The view grammar checks every field without requiring a preceding sketch-block manager.
    writer = PartArchiveWriter(graph_allocation(graph, owner.IndexValue))
    writer.begin_object(owner.ClassValue.NameValue, owner.ClassValue.SchemaValue)
    writer.u16(1)
    writer.begin_object(ANNOTATION_CLASS.NameValue, ANNOTATION_CLASS.SchemaValue)
    WriteViewBase(writer, *KTop, ANNOTATION_BASE_ID + 1)
    WriteAnnoTail(writer)
    if (
        writer.build() != config[owner.StartOffset:owner.EndOffset]
        or writer.Snapshot() != graph_allocation(graph, view.IndexValue + 1)
    ):
        raise ValueError("Top annotation uses an unsupported pose, reference or subtype field")
    return view


def extract_top_annotation(raw: bytes, source_document: CadDocument) -> tuple[dict, dict]:
    if type(raw) is not bytes or type(source_document) is not CadDocument:
        raise TypeError("Top annotation extraction requires native bytes and their typed source document")
    source_sha = digest(raw)
    source = source_document.source
    if source.format_id != KPartFormatId or source.sha256 != source_sha:
        raise ValueError("Top annotation source identity does not match the exact archive")
    archive = SldprtArchive.from_bytes(raw, "<source Top annotation>")
    graph = ReadPartConfig(archive)
    configuration = bound_configuration(source_document, archive, graph.VersionValue)
    config = archive.Require("Contents/Config-0")
    view = checked_view(graph, config)
    matrix = view.FieldsValue["f368"]["f08"]
    axes = tuple(
        SpaceVector(*(matrix[f"m{index}"] or 0.0 for index in range(row, row + 3)))
        for row in (0, 3, 6)
    )
    transform = Transform(SpaceVector(0.0, 0.0, 0.0), *axes)
    intent = TopAnnotationIntent(configuration, transform)
    annotation = {
        "configuration_id": intent.configuration_id,
        "role": "top",
        "projection": "orthographic",
        "frame_direction": "view_to_model",
        "origin_unit": "mm",
        "transform": ToData(intent.transform),
    }
    fields = graph.RootValue.FieldsValue
    evidence = {
        "schema": "kit.sw2026.top-annotation-source-evidence.v1",
        "source_sha256": source_sha,
        "config_stream_sha256": digest(config),
        "native_owner": "moPart_c.fa48",
        "native_configuration_name": source_document.configurations[0].name,
        "object_slot": view.IndexValue,
        "object_span": [view.StartOffset, view.EndOffset],
        "annotation_sha256": digest(canonical_json(annotation)),
        "annotation_axes_binary64": [matrix[f"m{index}"].hex() for index in range(9)],
        "separate_display_state": {
            "feb4": fields["feb4"],
            "nec8": fields["nec8"],
            "fec0": [row["v"] for row in fields["fec0"]],
            "n1290": fields["n1290"],
            "f1288": [row["v"] for row in fields["f1288"]],
        },
    }
    return annotation, evidence


if __name__ == "__main__":
    parser = ArgumentParser(description="Extract the default Top annotation intent from a SOLIDWORKS source")
    parser.add_argument("source", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.source.read_bytes()
        document = open_document(raw, source_format=KPartFormatId, strict=True)
        annotation, evidence = extract_top_annotation(raw, document)
        with args.evidence.open("xb") as output:
            output.write(canonical_json(evidence))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    sys.stdout.buffer.write(canonical_json(annotation))
