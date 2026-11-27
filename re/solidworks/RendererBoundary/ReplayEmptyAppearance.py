from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from InspectResavedRenderer import (
    NATIVE_LIMIT, REVISION, canonical_json, demand, digest, guarded, read_record, same_map,
    verify_dependency, write_artifact,
)


VERSION = 19000
SOURCE_SHA = "15fbc8da9c56d5b1a99e8f568de369fd9b992e40386a04c577ab8c0e2d45e356"
DEFINITION_SHA = "99e7d629b1cb52b1b12b8a0818aee73a38578e039ede1bb7e4a823da3d7163d9"
REQUEST_LIMIT = 1024
DEFINITION_LIMIT = 1024 * 1024


def read_bounded(path, limit):
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    demand(len(raw) <= limit, "appearance replay input exceeds its byte limit")
    return raw


def read_owner(raw):
    from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import AppearanceState

    document = read_record(raw)
    demand(set(document) == {"AppearanceValue"} and canonical_json(document) == raw,
           "expected canonical appearance-only JSON")
    value = document["AppearanceValue"]
    demand(type(value) is dict and set(value) == {"ManagerOnWire", "NextAppearanceId"},
           "expected the existing two appearance state fields")
    owner = AppearanceState(**value)
    demand(owner.ManagerOnWire or owner.NextAppearanceId == 1,
           "an absent appearance manager requires the constructor seed")
    return owner


def read_definition(raw):
    from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyAppr import ReadEmptyAppr
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

    read = ReadModelDef(raw, VERSION)
    document = read.GraphValue.DocumentValue
    demand(document.ClassValue == RuntimeClass("uiPartDoc_c", 1)
           and read.UsageValue.IsComplete and not read.UsageValue.ByteFields,
           "expected a completely typed version-19000 part Definition")
    return read, ReadEmptyAppr(document.FieldsValue)


def inspect_generated(raw, expected):
    from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeAppearMgr import MakeAppearMgr
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef

    read, actual = read_definition(raw)
    demand(actual == expected, "generated appearance state differs from the request")
    fields = read.GraphValue.DocumentValue.FieldsValue
    manager = fields.get("f1110")
    authored = MakeAppearMgr(expected)
    demand(authored == {key: fields[key] for key in authored}, "signed wire fields differ from authored state")
    replay = WriteModelDef(read.GraphValue)
    demand(replay.OutputValue == raw, "generated Definition does not re-emit exactly")
    same_map(read.MapValue, replay.MapValue)
    return {
        "definition": {"bytes": len(raw), "sha256": digest(raw)},
        "appearance": asdict(actual),
        "signed_counter_words": None if manager is None else [manager["f08"], manager["f0c"]],
        "reference_count": None if manager is None else manager["list"]["n"],
        "reference_rows": None if manager is None else len(manager["list"]["items"]),
        "map_next": read.MapValue.CounterValue,
        "exact_replay": True,
    }


def extract(args):
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    raw = read_bounded(args.source, NATIVE_LIMIT)
    demand(digest(raw) == SOURCE_SHA, "expected the disclosed named native save")
    archive = SldprtArchive.from_bytes(raw, "<named native save appearance extraction>")
    demand(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
           "expected container format 4 and archive version 19000")
    definition = archive.Require("Contents/Definition")
    demand(digest(definition) == DEFINITION_SHA, "source Definition digest differs")
    _, owner = read_definition(definition)
    request = canonical_json({"AppearanceValue": asdict(owner)})
    demand(read_bounded(args.source, NATIVE_LIMIT) == raw, "source changed during extraction")
    write_artifact(args.output.parent, args.output.name, request)
    return {"source_sha256": SOURCE_SHA, "source_definition_sha256": DEFINITION_SHA,
            "request_sha256": digest(request), "appearance": asdict(owner)}


def build_definition(owner):
    from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
    from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
    from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeAppearMgr import MakeAppearMgr
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef

    def construct():
        settings = ModelDefInput("moISO_c", (17,), (26, 4, 25, True), False, "Journal", VERSION)
        graph = MakePartDef(settings, 1000.0)
        fields = graph.DocumentValue.FieldsValue
        demand(fields["has_pwmaterial"] == 0 and "f1110" not in fields,
               "fresh Definition already owns an appearance manager")
        fields.update(MakeAppearMgr(owner))
        return WriteModelDef(graph).OutputValue

    return guarded(construct)


def generate(args):
    request = read_bounded(args.request, REQUEST_LIMIT)
    owner = read_owner(request)
    definition = build_definition(owner)
    result = inspect_generated(definition, owner)
    demand(read_bounded(args.request, REQUEST_LIMIT) == request, "request changed during generation")
    write_artifact(args.output.parent, args.output.name, definition)
    return {"request_sha256": digest(request), "external_generation_attempts": 0, **result}


def verify(args):
    request = read_bounded(args.request, REQUEST_LIMIT)
    definition = read_bounded(args.definition, DEFINITION_LIMIT)
    owner = read_owner(request)
    result = inspect_generated(definition, owner)
    demand(definition == build_definition(owner), "Definition differs from the fresh independent settings")
    return {"request_sha256": digest(request), **result}


def main():
    parser = ArgumentParser(description="Replay empty appearance allocation in a fresh part Definition")
    parser.add_argument("--dependency-root", required=True, type=Path)
    commands = parser.add_subparsers(dest="stage", required=True)
    for action, inputs in ((extract, ("source", "output")), (generate, ("request", "output")),
                           (verify, ("request", "definition"))):
        command = commands.add_parser(action.__name__)
        command.set_defaults(action=action)
        for option in inputs:
            command.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    verify_dependency(args.dependency_root)
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef

    demand(Path(ReadModelDef.__code__.co_filename).resolve().is_relative_to(
        args.dependency_root.resolve() / "src"), "Definition import escaped its pinned checkout")
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    result = args.action(args)
    sys.stdout.buffer.write(canonical_json({"stage": args.stage, "dependency_revision": REVISION,
                                            "archive_version": VERSION, **result}))


if __name__ == "__main__":
    main()
