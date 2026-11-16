from __future__ import annotations

from dataclasses import replace

from Core import ArchiveError
from builders.Definition import definition_stream, part_definition
from builders.Part import construct_part
from builders.Views import standard_views
from convert.adapters.solidworks.Archive.Views.MakeViewPair import MakeViewPair
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


def camera_input(value):
    if type(value) is not dict or set(value) != {"named_view", "translation", "scale2"}:
        raise ArchiveError("orthographic camera requires an explicit standard view, translation and scale")
    index = value["named_view"]
    if type(index) is not int or not 1 <= index <= 9:
        raise ArchiveError("orthographic camera supports standard view indices one through nine")
    translation = value["translation"]
    if type(translation) is not list or len(translation) != 3:
        raise ArchiveError("orthographic camera requires three native translation coordinates")
    rotation = standard_views(detail_standard=1)[index]["o"]["f368"]
    matrix = tuple(rotation["f08"][f"m{offset}"] for offset in range(9)) if rotation["has_matrix"] else tuple(float(offset % 4 == 0) for offset in range(9))
    return ViewInput(matrix, tuple(translation), value["scale2"])


def construct_camera_part(*, registry, document, provenance, presentation, target):
    if type(presentation) is not dict or "initial_view" not in presentation:
        raise ArchiveError("camera part requires an explicit initial view")
    view = camera_input(presentation["initial_view"])
    base_presentation = {key: value for key, value in presentation.items() if key != "initial_view"}
    construction = construct_part(registry=registry, document=document, provenance=provenance, presentation=base_presentation, target=target)
    definition = part_definition(
        density_kg_m3=document["density_kg_m3"], drafting_standard=base_presentation["drafting_standard"],
        detail_flags=base_presentation["detail_flags"], tessellation=tuple(base_presentation["tessellation"]),
        system_preference_7a=base_presentation["system_preference_7a"], journal_name=base_presentation["journal_name"],
    )
    definition["fae8"], definition["faf0"] = MakeViewPair(view)
    streams = {**construction.streams, "Contents/Definition": definition_stream(registry=registry, document=definition)}
    return replace(construction, streams=streams)
