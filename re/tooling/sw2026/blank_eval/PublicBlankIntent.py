from hashlib import sha256
import json
from pathlib import Path

from interchange.Enums.EnumUnits import UnitSystem
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet


def pinned(path, expected):
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("expected an absolute ordinary input file")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError("input hash differs")
    return json.loads(raw)


def neutral_drawing(path, expected, name):
    value = pinned(path, expected)
    if set(value) != {
        "schema", "sheet_id", "sheet_name", "width_m", "height_m", "scale_ratio",
    } or value["schema"] != "kit.sw2026.public-blank-neutral-intent.v1":
        raise ValueError("unexpected neutral drawing fields")
    sheet_id, sheet_name = value["sheet_id"], value["sheet_name"]
    width, height = value["width_m"], value["height_m"]
    ratio = value["scale_ratio"]
    if (
        type(sheet_id) is not str or not sheet_id
        or type(sheet_name) is not str or not sheet_name
        or type(width) not in (int, float) or type(height) not in (int, float)
        or type(ratio) is not list or len(ratio) != 2
        or any(type(term) is not int for term in ratio)
    ):
        raise ValueError("invalid typed neutral drawing fields")
    sheet = DrawingSheet(sheet_id, sheet_name, width, height, tuple(ratio))
    return CadDocument(
        CadSource("neutral", "", expected),
        (), (), (), (), (), (), (),
        DrawingValue=DrawingData(sheet_id, (sheet,)),
        units=UnitSystem.KMeter,
        metadata={"name": name},
    )
