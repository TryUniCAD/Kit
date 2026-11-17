from __future__ import annotations

import argparse
import json
from pathlib import Path

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, compare_numeric, digest, nodes, require
from Classes import registry
from defs.Definition import load_definition
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KEYWORDS_STREAM
from convert.adapters.solidworks.Drawing.Metadata.JoinSheetProps import JoinSheetProps
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawKeywords import ReadSheetKeys
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawProps import ReadDrawProps

from builders.DrawingMetadata import INFORMATION_STREAM, drawing_layout_properties, drawing_sheet_indexes
from builders.DrawingSheet import DrawingSheet, drawing_sheet
from builders.Units import LENGTH_CODES


ZONE_FIELDS = ("f4a8", "f4b0", "f4b8", "f4c0", "f4c8", "f4cc")


def disclosed_sheet(root, case, rules):
    saved, authored, _ = checked_artifacts(root, case)
    archive = SldprtArchive.from_bytes(saved)
    definition, _ = load_definition(archive.require("Contents/Definition"), rules, 19000)
    doc = definition.head
    model = doc["model"]
    sheet = model["f1430"]
    length = next(row["o"]["fb0"] for row in model["f9b8"]["items"] if row["o"].cls == "moLengthUserUnits_c")
    length_unit = next(unit for unit, code in LENGTH_CODES.items() if code == length)
    expected = DrawingSheet(
        name=authored["sheet"], paper_size="ansi-a-landscape", length_unit=length_unit,
        scale_numerator=int(authored["sheet_properties"][2]), scale_denominator=int(authored["sheet_properties"][3]),
        custom_property_view=sheet["f3d0"],
    )
    computed = expected.authored_fields()
    compare_numeric("drawing zone defaults", [computed[k] for k in ZONE_FIELDS], [sheet[k] for k in ZONE_FIELDS])
    compare_numeric("drawing paper record", [computed[k] for k in ("f39c", "f3f0", "f3e8", "f3f8", "f400")],
                    [sheet[k] for k in ("f39c", "f3f0", "f3e8", "f3f8", "f400")])
    plane, profile, detail, *_ = nodes(sheet)
    require(plane.cls == "moRefPlane_c" and profile.cls == "moProfileFeature_c" and detail.cls == "moDetailFolder_c", "unexpected drawing sheet owner order")
    require(sheet["f408"] is profile and sheet["f390"] is detail, "drawing sheet support objects lost their aliases")
    require(doc["fac0"]["profile_feature_id"] == profile["f08"] and profile["pd_f78"]["ff8"] is plane,
            "drawing sketch and plane identity differs")
    require(profile["pd_ff0"] == plane["f6f8"]["f20"] == expected.model_sketch_frame(),
            "drawing plane/profile scale differs from inverse sheet ratio")
    require(doc["fac0"]["f80"] == expected.ui_sketch_frame(), "UI sketch scale differs from forward sheet ratio")
    return {
        "name": case["name"], "source_sha256": digest(saved), "length_unit": length_unit,
        "zone_counts": [computed["f4c8"], computed["f4cc"]],
        "zone_margins": [computed[k] for k in ZONE_FIELDS[:4]],
        "sheet_scale": expected.scale,
        "model_sketch_scale": expected.model_sketch_frame()["f70"],
        "ui_sketch_scale": expected.ui_sketch_frame()["f70"],
    }


def generated_profile(*, name, length_unit, scale_numerator, scale_denominator, sheet_id):
    settings = drawing_sheet({
        "name": name, "length_unit": length_unit, "paper_size": "ansi-a-landscape",
        "scale_numerator": scale_numerator, "scale_denominator": scale_denominator,
        "custom_property_view": "Default",
    })
    streams = drawing_sheet_indexes(document_name="GeneratedZones", created_at=1000000000, sheet=settings, sheet_id=sheet_id)
    keywords = ReadSheetKeys(streams[KEYWORDS_STREAM])
    properties = ReadDrawProps(streams[INFORMATION_STREAM], frozenset(drawing_layout_properties(sheet=settings)))
    size = JoinSheetProps(properties, keywords)
    require((keywords.IdValue, keywords.NameValue, keywords.ScaleRatio) == (sheet_id, name, (scale_numerator, scale_denominator)),
            "generated keyword values differ from independently authored sheet settings")
    compare_numeric("generated package paper dimensions", size, settings.dimensions)
    require(keywords.ViewName == keywords.ModelName == keywords.ConfigName == "", "empty sheet indexes advertised a linked view")
    values = settings.authored_fields()
    return {
        "sheet": name, "length_unit": length_unit, "ratio": [scale_numerator, scale_denominator],
        "zones": [values["f4c8"], values["f4cc"]],
        "streams": {key: {"bytes": len(data), "sha256": digest(data)} for key, data in sorted(streams.items())},
    }


def main():
    parser = argparse.ArgumentParser(description="Check the paper, zones and sketch frames of the disclosed drawing sheets")
    parser.add_argument("corpus", type=Path)
    args = parser.parse_args()
    lock = SOURCE_LOCK.read_bytes()
    cases = {case["name"]: case for case in json.loads(lock)["cases"] if case["name"] in DISCLOSED}
    rules = registry()
    result = {
        "schema": "kit.sw2026.drawing-sheet-fields.v1",
        "source_lock_sha256": digest(lock),
        "disclosed": [disclosed_sheet(args.corpus, cases[name], rules) for name in DISCLOSED],
        "generated_index_checks": [
            generated_profile(name="Metric Paper", length_unit="mm", scale_numerator=3, scale_denominator=2, sheet_id=9),
            generated_profile(name="Imperial Paper", length_unit="in", scale_numerator=2, scale_denominator=7, sheet_id=12),
        ],
        "native_acceptance": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
