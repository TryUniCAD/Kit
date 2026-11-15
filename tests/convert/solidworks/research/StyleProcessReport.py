from __future__ import annotations

from builtins import getattr as GetAttr
from hashlib import sha256 as HashBytes
from typing import cast as CastValue


# decoded field observations let the parent verify authored intent across the codec boundary
def InspectResult(
    StyleRoot: object, UnitRoot: object, StyleBytes: bytes, UnitBytes: bytes
) -> dict[str, object]:
    StyleData = CastValue(dict[str, object], GetAttr(StyleRoot, "f"))
    UnitData = CastValue(dict[str, object], GetAttr(UnitRoot, "f"))
    UnitItems = CastValue(list[dict[str, object]], UnitData["items"])
    UnitNodes = [Entry["o"] for Entry in UnitItems]
    TaskData = CastValue(dict[str, object], StyleData["fb8"])
    DimData = CastValue(dict[str, object], StyleData["f13b0"])
    Annotations = CastValue(dict[str, object], StyleData["f1f18"])
    return {
        "style_size": len(StyleBytes),
        "unit_size": len(UnitBytes),
        "style_hash": HashBytes(StyleBytes).hexdigest(),
        "unit_hash": HashBytes(UnitBytes).hexdigest(),
        "standard": StyleData["f10"],
        "font": CastValue(dict[str, object], StyleData["f90"])["f08"],
        "exclusions": StyleData["f58"],
        "exclusion_count": StyleData["n58"],
        "task_labels": TaskData["items"],
        "task_count": TaskData["n"],
        "cutlist": [StyleData[Field] for Field in ("f200", "f208", "f210")],
        "linear_font": CastValue(
            dict[str, object], CastValue(dict[str, object], DimData["fe0"])["fe8"]
        )["f08"],
        "annotation_align": CastValue(dict[str, object], Annotations["f418"])["f1c"],
        "print_widths": list(CastValue(dict[str, object], StyleData["fb0"]).values()),
        "gtol_frames": CastValue(dict[str, object], StyleData["f9a0"])["n08"],
        "unit_count": UnitData["n"],
        "unit_classes": [GetAttr(NodeValue, "cls") for NodeValue in UnitNodes],
        "unit_codes": [
            CastValue(dict[str, object], GetAttr(NodeValue, "f")).get("fb0")
            for NodeValue in UnitNodes
        ],
        "unit_precision": [
            CastValue(dict[str, object], GetAttr(NodeValue, "f"))["f0c"]
            for NodeValue in UnitNodes
        ],
    }
