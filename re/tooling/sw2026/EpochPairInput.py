from __future__ import annotations

from dataclasses import replace
from ntpath import join

from EpochClocks import ClockPlan, drawing_clocks, require
from OriginPairInput import make_job
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


def make_epoch_request(spec, case):
    clocks = ClockPlan.from_data(case["part_clocks"])
    baseline = ClockPlan.from_data(next(value["part_clocks"] for value in spec["cases"]
                                        if value["changed_axis"] == "none"))
    geometry = spec["neutral_geometry"]
    drawing = spec["drawing"]
    label = "EpochDrawing"
    job = make_job(label, geometry["width_m"], geometry["height_m"], geometry["depth_m"],
                   "*" + drawing["named_view"], drawing["scale"], tuple(drawing["view_position_m"]))
    document = FromData(job["part"]["document"])
    sketch = replace(document.sketches[0], name=geometry["profile_name"])
    boss = replace(document.feature_timeline[0], name=geometry["boss_name"])
    bodies = tuple(replace(value, name=boss.name) for value in document.bodies)
    document = replace(document, sketches=(sketch,), feature_timeline=(boss,), bodies=bodies,
                        metadata={**document.metadata, "name": "EpochPart"})
    job["part"]["document"] = ToData(document)
    settings = job["part"]["settings"]
    common = spec["common_metadata"]
    settings["system"]["created_at"] = clocks.CreatedAt
    settings["provenance"].update(author=common["AuthorName"], company=common["CompanyName"],
                                   comment=common["CommentText"], created_at=clocks.CreatedAt,
                                   modified_at=baseline.ModifiedAt, updated_at=clocks.UpdatedAt)
    directory = join(r"C:\KitEpochDiscovery", case["name"])
    child_path = join(directory, spec["output_identity"]["part_basename"])
    drawing_path = join(directory, spec["output_identity"]["drawing_basename"])
    settings["output"].update(path_name=child_path, saved_at=clocks.SelfSavedAt)
    draw_clocks = drawing_clocks(drawing["clocks"])
    native = job["native"]
    native["options"]["created_at"] = draw_clocks["CreatedAt"]
    native["options"]["name"] = "EpochDrawing"
    native["provenance"].update(author=common["AuthorName"], company=common["CompanyName"],
                                comment=common["CommentText"], created_at=draw_clocks["CreatedAt"],
                                modified_at=draw_clocks["ModifiedAt"], updated_at=draw_clocks["UpdatedAt"])
    native["output"].update(path_name=drawing_path, saved_at=draw_clocks["SelfSavedAt"])
    neutral = FromData(job["drawing_document"])
    sheet = neutral.Sheets[0]
    view = replace(sheet.Views[0], EntityName=drawing["view_name"])
    sheet = replace(sheet, SheetWidth=drawing["sheet_width_m"], SheetHeight=drawing["sheet_height_m"],
                    ScaleRatio=tuple(drawing["sheet_scale"]), Views=(view,))
    reference = replace(neutral.ModelRefs[0], SourcePath=child_path)
    job["drawing_document"] = ToData(replace(neutral, Sheets=(sheet,), ModelRefs=(reference,)))
    return {"schema": "kit.sw2026.sdk-epoch-pair-request.v1", "case": case["name"],
            "origin_request": job, "clock_plan": clocks.to_data(),
            "drawing_clock_plan": draw_clocks, "changed_axis": case["changed_axis"]}
