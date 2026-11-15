import hashlib
import io
import json
import os
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / "src"))

import BuildVariants

from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile

OLD = Path(
    os.environ.get(
        "KIT_DRAWING_SRC",
        "/private/var/folders/b0/tf903gr929v3hkcly_v3dl800000gn/T/KitFusionDrawings/Variants",
    )
)
OUT = Path(os.environ.get("KIT_DRAWING_OUT", str(HERE / "Out"))) / "Variants"
SOURCE = os.environ.get("KIT_SCALE_SOURCE", "D1FreshLayout")
LABEL = os.environ.get("KIT_SCALE_LABEL", "C22ViewScale2")
SCALE = float(os.environ.get("KIT_SCALE_VALUE", "2.0"))
SCALE_NAME = os.environ.get("KIT_SCALE_NAME", "2:1")


def source_parts(label):
    with zipfile.ZipFile(io.BytesIO((OLD / f"{label}.f3z").read_bytes())) as archive:
        names = archive.namelist()
        drawing_name = next(name for name in names if name.endswith(".f2d"))
        design_name = next(name for name in names if name.endswith(".f3d"))
        return archive.read(design_name), archive.read(drawing_name)


def rewrite(entry, values):
    record = type(entry.ClassData)(
        tuple(
            DwgField(field.FieldName, values.get(field.FieldName, field.FieldValue))
            for field in entry.ClassData.RecordFields
        )
    )
    return replace(entry, ClassData=record)


def retarget(model):
    objects = []
    views = 0
    scales = 0
    for entry in model.DwgObjects:
        if entry.ClassKind == "DRAWINGVIEW":
            objects.append(rewrite(entry, {"ViewScale": SCALE}))
            views += 1
            continue
        if entry.ClassKind == "SCALE":
            fields = {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}
            if fields.get("ScaleName") == "4:1":
                objects.append(
                    rewrite(
                        entry,
                        {
                            "ScaleName": SCALE_NAME,
                            "PaperUnits": SCALE,
                            "DrawingUnits": 1.0,
                        },
                    )
                )
                scales += 1
                continue
        objects.append(entry)
    return replace(model, DwgObjects=tuple(objects)), views, scales


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BuildVariants.OUT = OUT
    design, f2d = source_parts(SOURCE)
    model = ReadDwgFile(BuildVariants.database(f2d))
    retargeted, views, scales = retarget(model)
    data = EmitDwgFile(retargeted)
    again = ReadDwgFile(data)
    after = [
        {field.FieldName: field.FieldValue for field in entry.ClassData.RecordFields}
        for entry in again.DwgObjects
        if entry.ClassKind == "DRAWINGVIEW"
    ]
    bundle = BuildVariants.opaque_bundle(
        BuildVariants.without_database(f2d, data), design, LABEL
    )
    path = OUT / f"{LABEL}.f3z"
    path.write_bytes(bundle)
    row = {
        "label": LABEL,
        "source": SOURCE,
        "file": path.name,
        "bytes": len(bundle),
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "dwg_bytes": len(data),
        "dwg_sha256": hashlib.sha256(data).hexdigest(),
        "views_changed": views,
        "scales_changed": scales,
        "view_scales_after": [entry.get("ViewScale") for entry in after],
    }
    (OUT / "PlanScale.json").write_text(json.dumps({"variants": [row]}, indent=1) + "\n")
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
