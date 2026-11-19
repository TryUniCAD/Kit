from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
from json import dumps
from pathlib import Path, PureWindowsPath
from uuid import UUID

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import MakeSelfFile
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import KDefPrefixFields
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Core.DrawingWriting.MakeBlankWriteRecipe import MakeBlankWriteRecipe
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawHeader import MakeDrawHeader
from convert.adapters.solidworks.Drawing.Construction.Metadata.MakeDrawStreams import MakeDrawStreams
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawRoot import MakeDrawRoot
from convert.adapters.solidworks.Drawing.Construction.Portable.CheckBlankInput import CheckBlankInput
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankBuild import MakeBlankBuild
from convert.adapters.solidworks.Drawing.Construction.Ui.MakeDrawDef import MakeDrawDef
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankDoc import CheckBlankDoc
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import ReadBlankKids
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import WalkDrawNodes
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawMut import WriteDrawMut
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import KFrontLayouts
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import KFrontSchemas
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import KFrontVirtuals
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadLinkedBody import ReadLinkedBody
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteDrawing import ResolvePlainNote
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteRows import NeedOneNoteRow
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteText import ReadNoteText
from convert.adapters.solidworks.Drawing.Definition.Writing.CheckSheetData import CheckSheetData
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.geometry.Models.VectorSpace import SpaceVector

from NoteConstruction import construct_local_hierarchy, object_rows, publish_first_note_identity, register_origin_anchor


def emit_definition(doc, version):
    CheckBlankDoc(doc)
    context = BodyContext(version, KFrontLayouts, KFrontVirtuals, KFrontSchemas)
    context.FlagsValue["owner_is_drawing"] = 1
    writer = BodyWriter(ArchiveMaps(1), context, WriteDrawMut)
    for value in WalkDrawNodes(doc.DocumentValue):
        descriptor = value.ClassValue
        if not (isinstance(descriptor, RuntimeClass) and (descriptor.NameValue, descriptor.SchemaValue) in KHeaderClasses):
            CheckBodyMut(context, value)
        if descriptor == RuntimeClass("moDrSheet", 1):
            CheckSheetData(writer, value)
    frame = WriteFrame(writer, FieldScope(doc.DocumentValue.FieldsValue), doc.DocumentValue, WriteSchemaMut, WriteFieldsMut)
    WriteFieldsMut(frame, KDefPrefixFields)
    writer.OutputValue.extend(KDrawClsid)
    WriteBodyMut(writer, doc.DocumentValue)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def local_state(folder, note):
    data = note.FieldsValue["f48"].FieldsValue["fe8"]
    text = data.FieldsValue["f98"]
    note.FieldsValue["f30"] = folder
    data.FieldsValue["f48"] = folder
    text.FieldsValue["f170"] = note
    if folder.FieldsValue["f358"]["n"] != 0:
        raise ValueError("fresh drawing already contains a note list")
    folder.FieldsValue["f358"] = object_rows((note,))


def build(input_value, *, origin_anchor, publish_identity=False):
    CheckBlankInput(input_value)
    layout = input_value.DrawingValue
    if len(layout.Sheets) != 1 or layout.ModelRefs:
        raise ValueError("fresh plain note requires one unlinked sheet")
    sheet, = layout.Sheets
    if sheet.Views or sheet.Notes is None or len(sheet.Notes) != 1:
        raise ValueError("fresh plain note needs exactly one standalone note")
    annotation, = sheet.Notes
    base_layout = replace(layout, Sheets=(replace(sheet, Notes=None),))
    graph = MakeDrawRoot(MakeBlankBuild(base_layout, input_value.OptionsValue))
    header = MakeDrawHeader(graph, input_value.HeaderValue)
    header.FieldsValue["f38"] = MakeSelfFile(graph.ModelValue, header, None, input_value.FileValue)
    graph.ModelValue.FieldsValue["fa8"] = header
    doc = MakeDrawDef(input_value.UiSettings, graph)
    children = ReadBlankKids(graph.SheetValue.SheetValue)
    folder = graph.SheetValue.SheetValue.FieldsValue["f390"]
    if len(children) != 3 or children[-1] is not folder:
        raise ValueError("drawing sheet has no actual final detail owner")
    details = graph.ModelValue.FieldsValue["fae0"]
    display = construct_local_hierarchy(annotation, details, doc.VersionValue)
    if publish_identity:
        publish_first_note_identity(graph.ModelValue, folder, display, input_value.OptionsValue.StyleValue.LanguageId)
    local_state(folder, display)
    if origin_anchor:
        register_origin_anchor(display, annotation.PositionValue)
    definition, write_map = emit_definition(doc, doc.VersionValue)
    read, read_map, _ = ReadLinkedBody(definition, doc.VersionValue, "fresh note local hierarchy")
    read_model = read.FieldsValue["model"]
    read_sheet = read_model.FieldsValue["f1430"]
    read_folder = read_sheet.FieldsValue["f390"]
    read_display = NeedOneNoteRow(read_folder, "f358", "moDisplayNote_c")
    read_data = read_display.FieldsValue["f48"].FieldsValue["fe8"]
    read_text = read_data.FieldsValue["f98"]
    if publish_identity and (
        read_data.FieldsValue["f18"].FieldsValue["f08"] != "DetailItem1"
        or read_display.FieldsValue["f58"] != display.FieldsValue["f58"]
        or read_model.FieldsValue["fd44"] != graph.ModelValue.FieldsValue["fd44"]
        or read_data.FieldsValue["f08"] != -1
    ):
        raise ValueError("generated note name or independent display identity differs")
    if origin_anchor and ResolvePlainNote(read_sheet) is not read_text:
        raise ValueError("generated origin-anchor note does not bind its real text owner")
    if (
        read_display.FieldsValue["f30"] is not read_folder
        or read_data.FieldsValue["f48"] is not read_folder
        or read_text.FieldsValue["f170"] is not read_display
        or ReadNoteText(read_text) != annotation.TextValue
        or tuple(read_text.FieldsValue["f38"][axis] for axis in "xyz")
        != (annotation.PositionValue.x, annotation.PositionValue.y, annotation.PositionValue.z)
        or write_map.CounterValue != read_map.CounterValue
    ):
        raise ValueError("fresh note typed readback diverges from authored state")
    reencoded, reencoded_map = emit_definition(replace(doc, DocumentValue=read), doc.VersionValue)
    if reencoded != definition or reencoded_map.CounterValue != write_map.CounterValue:
        raise ValueError("fresh note Definition does not re-encode exactly")
    streams = MakeDrawStreams(input_value, header, graph.SheetValue.SheetValue, definition)
    return build_sldprt(streams), streams, write_map


def note_input(text, position, sheet_name, scale, path, epoch, block_id):
    annotation = DrawingNote("plain-note-surface/note/1", text, SpaceVector(*position))
    sheet = DrawingSheet("plain-note-surface", sheet_name, 0.2794, 0.2159, tuple(scale), Notes=(annotation,))
    layout = DrawingData(sheet.EntityId, (sheet,))
    locator = PureWindowsPath(path)
    if not locator.is_absolute() or locator.suffix.casefold() != ".slddrw":
        raise ValueError("generated note locator requires an absolute native drawing path")
    return MakeBlankWriteRecipe(layout, SelfFileInput(str(locator), epoch), block_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--position", required=True, nargs=3, type=float)
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--scale", required=True, nargs=2, type=float)
    parser.add_argument("--locator", required=True)
    parser.add_argument("--origin-anchor", action="store_true")
    parser.add_argument("--publish-identity", action="store_true")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--epoch", required=True, type=int)
    parser.add_argument("--block-id", required=True, type=UUID)
    args = parser.parse_args()
    input_value = note_input(args.text, args.position, args.sheet, args.scale, args.locator, args.epoch, args.block_id)
    payload, streams, maps = build(input_value, origin_anchor=args.origin_anchor, publish_identity=args.publish_identity)
    if args.out.suffix.upper() != ".SLDDRW":
        raise ValueError("native output extension required")
    with args.out.open("xb") as output:
        count = output.write(payload)
    if count != len(payload):
        raise OSError("short raw drawing write")
    print(dumps({
        "sha256": sha256(payload).hexdigest(),
        "bytes": len(payload),
        "map_counter": maps.CounterValue,
        "streams": {name: len(value) for name, value in streams.items()},
        "attachment_registered": args.origin_anchor,
        "native_qualified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
