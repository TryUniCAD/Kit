from argparse import ArgumentParser
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from pathlib import Path, PureWindowsPath
import sys
from uuid import UUID

from convert import open_document
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Core.DrawingWriting.MakeBlankWriteRecipe import MakeBlankWriteRecipe
from convert.adapters.solidworks.Drawing.Construction.Notes.MakePlainNoteFile import MakePlainNoteFile
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadLinkedBody import ReadLinkedBody
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.WritePlainNoteDef import WritePlainNoteDef
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.geometry.Models.VectorSpace import SpaceVector


def make_input(record):
    locator = PureWindowsPath(record["locator"])
    if not locator.is_absolute() or locator.suffix.casefold() != ".slddrw":
        raise ValueError("SDK note recipe requires an absolute native drawing locator")
    annotation = DrawingNote(
        "plain-note-surface/note/1", record["initial_text"], SpaceVector(*record["initial_position"]),
    )
    sheet = DrawingSheet(
        "plain-note-surface", record["sheet"], 0.2794, 0.2159, tuple(record["scale"]),
        Notes=(annotation,),
    )
    recipe = MakeBlankWriteRecipe(
        DrawingData(sheet.EntityId, (sheet,)),
        SelfFileInput(str(locator), record["epoch"]),
        UUID(record["block_id"]),
    )
    standard = record.get("detailing_standard", 1)
    if type(standard) is not int or standard not in (0, 1):
        raise ValueError("unsupported drawing note detailing standard")
    switches = (
        (0, record.get("display_annotations", False)),
        (29, record.get("display_all_annotations", False)),
    )
    if any(type(action) is not bool for _, action in switches):
        raise TypeError("drawing annotation visibility requires explicit booleans")
    options = recipe.OptionsValue
    return replace(
        recipe,
        OptionsValue=replace(options, StyleValue=replace(options.StyleValue, StandardValue=standard)),
        UiSettings=replace(recipe.UiSettings, DisplayBits=tuple(index for index, action in switches if action)),
    )


def verify(value, record):
    definition = value.StreamsValue["Contents/Definition"]
    version = value.UiGraph.VersionValue
    raw, maps, usage = ReadLinkedBody(definition, version, "guarded SDK standalone note")
    rewritten = WritePlainNoteDef(replace(value.UiGraph, DocumentValue=raw))
    if (
        rewritten.OutputValue != definition
        or maps != rewritten.MapValue
        or usage.MissingNames
        or not rewritten.UsageValue.IsComplete
    ):
        raise ValueError("SDK note Definition did not retain exact bytes and archive maps")
    document = open_document(value.BytesValue, source_format="solidworks.slddrw", strict=False)
    sheet, = document.DrawingValue.Sheets
    annotation, = sheet.Notes or ()
    position = annotation.PositionValue
    if (
        sheet.EntityName != record["sheet"]
        or list(sheet.ScaleRatio) != record["scale"]
        or sheet.Views
        or document.DrawingValue.ModelRefs
        or annotation.TextValue != record["initial_text"]
        or [position.x, position.y, position.z] != record["initial_position"]
    ):
        raise ValueError("partial SDK note read changed authored drawing semantics")
    return maps.CounterValue


def main():
    parser = ArgumentParser()
    parser.add_argument("--guard-directory", type=Path, required=True)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--intent-sha256", required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source = args.intent.read_bytes()
    if sha256(source).hexdigest() != args.intent_sha256:
        raise ValueError("explicit note intent identity changed")
    record = loads(source)
    if not record["origin_anchor"] or not record["publish_identity"]:
        raise ValueError("SDK constructor requires ordinary display and note identity")
    sys.path.insert(0, str(args.guard_directory))
    from BlankRewriteGuard import OutputGuard

    for name in ("DocumentFeatureValidate", "DocumentReferenceValidate", "DocumentAssemblyValidate"):
        import_module("interchange.document.Validation." + name)
    import_module("interchange.document.Models.DocumentProvenance")
    for encoding in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        codecs.lookup(encoding)
    guard = OutputGuard(args.target.parent)
    sys.addaudithook(guard.event)
    guard.active = True
    try:
        value = MakePlainNoteFile(make_input(record), DisplayGrid=record.get("display_grid", True))
        with args.target.open("xb") as target:
            if target.write(value.BytesValue) != len(value.BytesValue):
                raise OSError("short generated SDK note write")
    finally:
        guard.active = False
    if guard.denied or guard.operations != ["output_write"]:
        raise ValueError("SDK note generation accessed undeclared data")
    counter = verify(value, record)
    with args.report.open("x", encoding="utf-8", newline="\n") as output:
        output.write(dumps({
            "schema": "kit.sw2026.sdk-plain-note-worker.v1",
            "passed": True,
            "runtime_input_reads": 0,
            "output_operations": guard.operations,
            "native_qualified": False,
            "public_output_qualified": False,
            "sdk_partial_note_visible": True,
            "definition_reemit_exact": True,
            "container_sha256": sha256(value.BytesValue).hexdigest(),
            "container_bytes": len(value.BytesValue),
            "definition_length": len(value.StreamsValue["Contents/Definition"]),
            "logical_streams": {name: sha256(data).hexdigest() for name, data in value.StreamsValue.items()},
            "intent_sha256": args.intent_sha256,
            "map_counter": counter,
        }, sort_keys=True, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
