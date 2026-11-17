from __future__ import annotations

import argparse
import json
import math
import ntpath
from pathlib import Path

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, compare_numeric, digest, nodes, require, view_transform
from Classes import registry
from Core import Load, Store
from Schema import Base
from defs.Drawing import DRAWING_CLSID
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import CheckDrawLane


DEFINITION = "Contents/Definition"
DRAWING_CLASS = "moDrawing_c"
LIGHTWEIGHT = "moModel_c.FUN_4c22ec80"
RESOLVED = "moModel_c.FUN_4c234150"
RESOLVED_CONCEPT = "moConcept_c.SerializeResolvedData"
FOLDERS = frozenset({
    "moCommentsFolder_c", "moBlockFolder_c", "moDocsFolder_c", "moDetailCabinet_c",
    "moInkMarkupFolder_c", "moMarkupCommentFolder_c",
})


def concept_registry():
    rules = registry()
    drawing = rules.classes[DRAWING_CLASS]
    resolved = rules.classes[RESOLVED]
    require(
        all(isinstance(step, Base) for step in (drawing[0], drawing[1], resolved[0]))
        and (drawing[0].cls, drawing[1].cls, resolved[0].cls) == (LIGHTWEIGHT, RESOLVED, RESOLVED_CONCEPT),
        "drawing prefix no longer follows the native lightweight and concept owners",
    )
    rules.classes[DRAWING_CLASS] = [drawing[0], resolved[0]]
    return rules


def read_concept(data, rules, version):
    with rules.track_usage("load", DEFINITION, role="drawing-concept-prefix") as usage:
        reader = Load(data, 1, rules, version, {"owner_is_drawing": 1})
        leading = tuple(reader.prim("i32") for _ in range(5))
        clsid = reader.prim("u32"), reader.prim("u16"), reader.prim("u16"), reader.raw(8)
        require(clsid == DRAWING_CLSID, "drawing prefix has the wrong document CLSID")
        model = reader.obj()
        require(model is not None and model.cls == DRAWING_CLASS and model.schema == 1, "drawing prefix has the wrong native class")
    writer = Store(1, rules, version, {"owner_is_drawing": 1})
    for item in leading:
        writer.prim("i32", item)
    writer.prim("u32", clsid[0])
    writer.prim("u16", clsid[1])
    writer.prim("u16", clsid[2])
    writer.raw(clsid[3])
    writer.obj(model)
    require(bytes(writer.out) == data[:reader.p] and writer.count == reader.count, "typed prefix did not round trip")
    return model, reader, usage.snapshot()


def project_view(view, directory, authored):
    require(view.cls == "moAbsoluteView" and authored is not None, "unqualified drawing view class")
    require(view["f18"]["f08"] == authored["name"] and view["f1018"] == authored["orientation"], "drawing view name or orientation differs from native")
    ratio = [view["f780"], view["f788"]]
    require(all(math.isfinite(value) and value > 0 for value in ratio), "unusable drawing view scale")
    compare_numeric("view scale", [ratio[0] / ratio[1]], [authored["scale"]])
    matrix = view_transform(view)
    compare_numeric("model-to-view transform", matrix, authored["model_to_view"][:13])
    reference = view["f5d8"]
    require(reference.cls == "moReferenceInternal_c" and reference["f3b0"] is directory, "view must point to its model directory entry")
    require(reference["f3c0"]["f08"] == authored["configuration"], "drawing view configuration differs from native")
    shared = directory["shared"]
    require(shared["f20"] == 2, "drawing view requires an external part")
    require(ntpath.normcase(ntpath.normpath(shared["h18"]["f08"])) == ntpath.normcase(ntpath.normpath(authored["resolved_reference_path"])), "drawing view linked the wrong external part")
    return {"orientation": view["f1018"], "scale_ratio": ratio, "model_to_view": matrix}


def project_model(model, authored):
    ordinary = nodes(model)
    sheets = [node for node in ordinary if node.cls == "moDrSheet"]
    require(len(sheets) == 1 and all(node.cls in FOLDERS or node is sheets[0] for node in ordinary), "unqualified drawing concept")
    sheet = sheets[0]
    require(sheet["f18"]["f08"] == authored["sheet"] and sheet["f3c0"] == 13, "drawing sheet has an unsupported format")
    compare_numeric("sheet width and height", [sheet["f3f0"], sheet["f3e8"]], authored["sheet_properties"][5:7])
    positioned = nodes(sheet)
    view_list = [node for node in positioned if node.cls == "moAbsoluteView"]
    require(all(node.cls in {"moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c", "moAbsoluteView"} for node in positioned), "unqualified sheet content")
    directory = model["fa8"]["f30"]
    if authored["view"] is None:
        require(not view_list and directory is None, "empty drawing has model view data")
        return ()
    require(len(view_list) == 1 and directory is not None and len(directory["items"]) == 1, "unqualified drawing external model ownership")
    return (project_view(view_list[0], directory["items"][0]["o"], authored["view"]),)


def check_case(root, case):
    saved, authored, _ = checked_artifacts(root, case)
    archive = SldprtArchive.from_bytes(saved)
    version = CheckDrawLane(archive)
    data = archive.require(DEFINITION)
    model, reader, usage = read_concept(data, concept_registry(), version)
    views = project_model(model, authored)
    require(usage["completed"] and not usage["missing_schemas"], "native prefix has unresolved schema owners")
    return {
        "name": case["name"], "source_sha256": digest(saved),
        "definition_bytes": len(data), "concept_prefix_bytes": reader.p,
        "concept_prefix_sha256": digest(data[:reader.p]), "map_next_index": reader.count,
        "native_views": views, "method_count": len(usage["used_schemas"]),
        "provisional_methods": usage["provisional_schemas"],
    }


def main():
    parser = argparse.ArgumentParser(description="Verify the smallest typed drawing concept walk against disclosed SOLIDWORKS sources")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--source-lock", type=Path, default=SOURCE_LOCK)
    args = parser.parse_args()
    lock = args.source_lock.read_bytes()
    cases = {case["name"]: case for case in json.loads(lock)["cases"] if case["name"] in DISCLOSED}
    result = {
        "schema": "kit.sw2026.drawing-concept-prefix.v1",
        "source_lock_sha256": digest(lock),
        "reader_qualified": False,
        "cases": [check_case(args.corpus, cases[name]) for name in DISCLOSED],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
