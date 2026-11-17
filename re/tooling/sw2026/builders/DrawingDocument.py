from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from Core import Obj, Store
from builders.Definition import _model_definition
from builders.DrawingMetadata import drawing_sheet_indexes
from builders.DrawingRoot import empty_drawing_root
from builders.DrawingSheet import drawing_sheet
from builders.DrawingSheetObjects import sheet_ui_sketch
from builders.ExternalFiles import ordinary_self_reference
from builders.Metadata import COUNTER_SEED, FILE_VERSION, biography, fields, header, history, rooted_metadata_streams
from builders.Model import PersistentIds
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.Drawing import DRAWING_CLSID


@dataclass(frozen=True, slots=True)
class BlankDrawingConstruction:
    streams: dict[str, bytes]
    model: Obj
    definition_map_count: int


def _definitions(*, registry, model, settings, presentation):
    options = dict(presentation)
    options["tessellation"] = tuple(options["tessellation"])
    document = _model_definition(cls="uiDrawingDoc_c", clsid_a=DRAWING_CLSID[0], **options)
    document.f.update({
        "model": model, "fac0": sheet_ui_sketch(settings=settings, sheet=model["f1430"]),
        "facc": 2, "drawing_end_marker": 0xDAF, "f16c8": 0, "f16dc": 0,
    })
    archive = Store(1, registry, FILE_VERSION)
    registry.run_store("uiModelDoc_c.Serialize", archive, document.f, document)
    registry.run_store("uiDrawingDoc_c.Serialize.own", archive, document.f, document)
    return bytes(archive.out), archive.count


def _metadata(*, registry, model, next_id, provenance, presentation, output):
    created = provenance["created_at"]
    modified = provenance["modified_at"]
    stamp = {"status": 0, "user_index": 0, "company_index": 0, "timestamp": created, "comment": provenance["comment"]}
    record = header(
        next_id=next_id, user_names=[provenance["author"]], company_names=[provenance["company"]],
        revision_logs=[{"object_id": model["f08"], "name": model["f18"]["f08"], "stamps": [stamp]}],
        created_at=created, modified_at=modified, updated_at=modified,
        model_present=True, component_count=0, update_stamp=COUNTER_SEED, body_stamp=COUNTER_SEED,
        license_flags=0, license_type=0,
    )
    record["f38"] = ordinary_self_reference(model=model, model_header=record, configuration=None, **output)
    model["fa8"] = record
    version = history(
        states=[{"file_version": FILE_VERSION, "date_codes": [{"build_code": provenance["originating_build_code"], "native_save": False}], "stamp": stamp}],
        failure_severity=0, minimum_free_memory=0xFFFFFFFF, license_origin=provenance["license_origin"],
        language_id=presentation["language_id"], cjk_saved=presentation["cjk_saved"], cjk_warning=False,
    )
    return rooted_metadata_streams(registry=registry, header2=record, model_headers={}, biography_record=biography(), history_record=version)


def construct_blank_drawing(*, registry, request):
    fields(request, "blank drawing", ("name", "sheet", "sheet_names", "folder_names", "provenance", "presentation", "target", "output"))
    settings = drawing_sheet(request["sheet"])
    presentation = fields(request["presentation"], "drawing presentation", ("styles", "units", "definition", "auto_dim_text_link", "language_id", "cjk_saved"))
    provenance = fields(request["provenance"], "drawing provenance", ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin", "block_identity"))
    target = fields(request["target"], "drawing target", ("date_code", "parasolid_version"))
    output = fields(request["output"], "drawing output", ("path_name", "saved_at"))
    if presentation["units"].get("length_unit") != settings.length_unit:
        raise ValueError("drawing sheet zones and model units require the same length unit")
    allocator = PersistentIds()
    model = empty_drawing_root(
        name=request["name"], allocator=allocator, settings=settings,
        folder_names=request["folder_names"], sheet_names=request["sheet_names"],
        detail_definitions=detail_definitions(**presentation["styles"]), document_units=unit_table_profile(**presentation["units"]),
        auto_dim_text_link=presentation["auto_dim_text_link"], block_identity=UUID(provenance["block_identity"]),
        created_at=provenance["created_at"], **target,
    )
    streams = _metadata(registry=registry, model=model, next_id=allocator.next_id, provenance=provenance,
                        presentation=presentation, output=output)
    definition, count = _definitions(registry=registry, model=model, settings=settings, presentation=presentation["definition"])
    streams["Contents/Definition"] = definition
    record = model["fa8"]
    stamps = Store(1, registry, FILE_VERSION)
    registry.run_store("ModelStamps.load", stamps, {"creation": record["f70"], "update_stamp": record["f40"], "body_stamp": record["f44"]}, model)
    streams["ModelStamps"] = bytes(stamps.out)
    streams.update(drawing_sheet_indexes(document_name=request["name"], created_at=provenance["created_at"], sheet=settings,
                                         sheet_id=model["f1430"]["f08"]))
    return BlankDrawingConstruction(streams=streams, model=model, definition_map_count=count)
