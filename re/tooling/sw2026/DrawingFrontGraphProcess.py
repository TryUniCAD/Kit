from __future__ import annotations

import codecs
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(path))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import Load, Obj, Store
from builders.DrawingDocument import construct_blank_drawing
from builders.DrawingFrontProjection import front_projection
from builders.DrawingSheet import drawing_sheet
from builders.DrawingTail import drawing_feature_filetime
from builders.DrawingViewLinks import single_view_links
from builders.DrawingViewSupports import front_view_supports
from builders.Metadata import fields
from builders.Model import PersistentIds, model_feature
from builders.Part import construct_part


def verify_links(*, model, header, internal, manager):
    entry, = (row["o"] for row in header["f30"]["items"])
    properties, = manager["f08"]
    reference = properties["model"]
    if manager["f18"] is not model or reference["f3b0"] is not entry or internal["f3b0"] is not entry:
        raise ValueError("drawing view records lost their common external file identity")
    if internal["f4f8"]["f50"] is not internal or internal["f4f8"]["f10"]["h18"] is not header["f38"]["shared"]["h18"]:
        raise ValueError("the internal view link lost its drawing file or feature backlink")
    if internal["f3c0"] != reference["f3c0"] or reference["f18"] is not None or reference["f08"] != -1:
        raise ValueError("drawing model property reference has unexpected configuration or identity")
    if entry["f48"] != 1 or properties["properties"]["n"] or reference["has_f370"] or reference["f4f8"] is not None:
        raise ValueError("drawing property reference changed the owning view connection")


def verify_supports(*, decoded, original, model):
    if [item.cls for item in decoded] != [item.cls for item in original]:
        raise ValueError("front-view support classes changed on readback")
    if [item["f08"] for item in decoded] != [item["f08"] for item in original]:
        raise ValueError("front-view support persistent IDs changed on readback")
    for plane, profile in (decoded[1:3], decoded[3:5]):
        handle = profile["pd_f78"]
        if handle["ff8"] is not plane or handle["ff0"]["f00"] != -1 or handle["f58"]["owner"] is not model:
            raise ValueError("front-view sketch lost its pre-insertion plane reference")
        if profile["pd_ff0"] != plane["f6f8"]["f20"] or profile["pd_f80"]["npoints"]:
            raise ValueError("front-view sketch no longer represents its generated empty plane")


def subgraph(*, drawing, view, links, rules):
    children = [row["o"] for row in view["f60"]["list"]["items"]]
    writer = Store(1, rules, 19000, {"owner_is_drawing": 1})
    writer.bind_direct_objects((drawing, view))
    for node in (drawing["fa8"], links.internal, links.properties):
        writer.obj(node)
    writer.ctx["conditions"] = 0x40
    for node in children:
        writer.obj(node)
    data = bytes(writer.out)
    reader = Load(data, 1, rules, 19000, {"owner_is_drawing": 1})
    model, view_root = Obj("moDrawing_c"), Obj("moAbsoluteView")
    reader.bind_direct_objects((model, view_root))
    header, internal, manager = reader.obj(), reader.obj(), reader.obj()
    reader.ctx["conditions"] = 0x40
    decoded = [reader.obj() for _ in children]
    verify_links(model=model, header=header, internal=internal, manager=manager)
    verify_supports(decoded=decoded, original=children, model=model)
    if reader.left() or reader.count != writer.count:
        raise ValueError("front-view support graph did not consume exactly")
    repeated = Store(1, rules, 19000, {"owner_is_drawing": 1})
    repeated.bind_direct_objects((model, view_root))
    for node in (header, internal, manager):
        repeated.obj(node)
    repeated.ctx["conditions"] = 0x40
    for node in decoded:
        repeated.obj(node)
    if bytes(repeated.out) != data or repeated.count != reader.count:
        raise ValueError("front-view support graph did not round-trip exactly")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "map_next_index": reader.count,
            "persistent_ids": [internal["f08"], view["f08"], *(node["f08"] for node in decoded)], "next_persistent_id": header["f08"]}


def main():
    request = fields(json.load(sys.stdin), "front view graph", ("drawing", "part", "view"))
    options = fields(request["view"], "front view", ("name", "orientation", "position", "scale", "supports"))
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    child = construct_part(registry=rules, **request["part"])
    drawing_spec = request["drawing"]
    drawing = construct_blank_drawing(registry=rules, request=drawing_spec).model
    sheet = drawing["f1430"]
    settings = drawing_sheet(drawing_spec["sheet"])
    target = drawing_spec["target"]
    created_at = drawing_spec["provenance"]["created_at"]
    allocator = PersistentIds(next_id=drawing["fa8"]["f08"])
    projection = front_projection(child=child, sheet=settings, orientation=options["orientation"], position=options["position"], scale=options["scale"])
    links = single_view_links(drawing=drawing, child=child, local_bounds=projection.view["f600"], allocator=allocator, created_at=created_at, target=target)
    view = model_feature(cls="moAbsoluteView", name=options["name"], owner=sheet, allocator=None, **target)
    view.f.update({**projection.view, **drawing_feature_filetime(created_at), "f0c": 0, "f5d8": links.internal})
    front_view_supports(view=view, drawing=drawing, projection=projection, names=options["supports"], allocator=allocator, created_at=created_at, target=target)
    drawing["fa8"].f.update(f08=allocator.next_id, bboxflag=1, bbox=projection.header_bounds)
    result = {"schema": "kit.sw2026.drawing-front-view-subgraph.v1", "native_acceptance": False, "view_projection": projection.view,
              "header_bounds": projection.header_bounds, "support_graph": subgraph(drawing=drawing, view=view, links=links, rules=rules),
              "input_runtime_file_access_attempts": len(AUDIT.DeniedReads)}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
