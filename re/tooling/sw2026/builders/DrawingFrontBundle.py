from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath

from Core import Obj
from Streams import StreamDoc, store_rooted
from builders.DrawingDocument import _definitions, construct_blank_drawing
from builders.DrawingFrontView import add_front_view
from builders.DrawingMetadata import DrawingViewIndex, drawing_sheet_indexes
from builders.DrawingSheet import drawing_sheet
from builders.Metadata import FILE_VERSION, fields
from builders.Part import PartConstruction, construct_part


@dataclass(frozen=True, slots=True)
class FrontDrawingBundle:
    streams: dict[str, bytes]
    view: Obj
    part: PartConstruction
    definition_map_count: int


def construct_front_bundle(*, registry, request):
    request = fields(request, "generated front drawing bundle", ("drawing", "part", "view"))
    part = construct_part(registry=registry, **request["part"])
    spec = request["drawing"]
    construction = construct_blank_drawing(registry=registry, request=spec)
    path = PureWindowsPath(spec["output"]["path_name"])
    if not path.is_absolute() or path.stem != spec["name"]:
        raise ValueError("drawing file identity must use its authored name and an absolute path")
    model = construction.model
    settings = drawing_sheet(spec["sheet"])
    created_at = spec["provenance"]["created_at"]
    view = add_front_view(drawing=model, child=part, sheet_settings=settings, requested=request["view"],
                          created_at=created_at, target=spec["target"])
    model_index = DrawingViewIndex.from_view(view)
    definition, map_count = _definitions(registry=registry, model=model, settings=settings, presentation=spec["presentation"]["definition"])
    header = store_rooted(StreamDoc("rooted", {"base": 1}, [model["fa8"]]), registry, FILE_VERSION)
    layout = drawing_sheet_indexes(document_name=spec["name"], created_at=created_at, sheet=settings,
                                   sheet_id=model["f1430"]["f08"], model_view=model_index)
    streams = {**construction.streams, "Contents/Definition": definition, "Header2": header, **layout}
    return FrontDrawingBundle(streams, view, part, map_count)
