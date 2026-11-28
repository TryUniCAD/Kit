from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from base64 import b64decode
from hashlib import sha256
import json

from OriginChildShape import inspect_child
from OriginPairChecks import check_display
from SpatialTextMut import require, text_rows
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef


def main():
    result = json.load(sys.stdin)
    require(result["schema"] == "kit.sw2026.spatial-text-result.v1" and result["passed"] is True,
            "spatial text preparation requires one complete generated pair")
    data = {name: b64decode(result[name + "_base64"], validate=True) for name in ("child", "drawing")}
    for name, raw in data.items():
        require(len(raw) == result[name + "_bytes"] and sha256(raw).hexdigest() == result[name + "_sha256"],
                "spatial text preparation input custody differs")
    child_archive = SldprtArchive.from_bytes(data["child"])
    draw_archive = SldprtArchive.from_bytes(data["drawing"])
    child = ReadNativeLink(child_archive, 0)
    profiles = tuple(node for node in child.ResolvedValue.RootsValue
                     if node is not None and node.ClassValue.NameValue == "moProfileFeature_c")
    require(len(profiles) == 1, "spatial text preparation found another actual profile")
    actual = text_rows(profiles[0])
    require(actual == result["text_after"], "spatial text changed an actual coordinate parameter or identity on load")
    config_bytes, config = WriteConfigMut(child.ConfigValue.RootValue, 19000, child.ConfigValue.HeaderValue)
    resolved_bytes, resolved = WriteResolMut(child.ResolvedValue.RootsValue, child.ResolvedValue.ExtraFields,
                                             19000, config.MapValue, child.ResolvedValue.ContextValue)
    require(config_bytes == child_archive.require("Contents/Config-0")
            and resolved_bytes == child_archive.require("Contents/Config-0-ResolvedFeatures"),
            "spatial text complete linked child fields did not replay byte for byte")
    drawing = ReadNamedDef(draw_archive.require("Contents/Definition"), 19000, result["orientation"])
    require(WriteNamedDef(drawing.GraphValue).OutputValue == draw_archive.require("Contents/Definition"),
            "spatial text complete drawing Definition did not replay byte for byte")
    profile = check_display(drawing.GraphValue, child.ResolvedValue.RootsValue, child.ConfigValue.HeaderValue)
    shape = inspect_child(child.ResolvedValue.RootsValue, result["child_shape"]["anchor_kind"])
    require(profile == result["profile"] and shape == result["child_shape"],
            "spatial text changed actual child origin topology or dimensional semantics")
    return {"schema": "kit.sw2026.spatial-text-preparation.v1", "passed": True,
            "child_sha256": result["child_sha256"], "drawing_sha256": result["drawing_sha256"],
            "text_after": actual, "profile": profile, "child_shape": shape,
            "config_byte_identity": True, "resolved_byte_identity": True, "definition_byte_identity": True,
            "resolved_map_next": resolved.MapValue.CounterValue,
            "source_original_admission": False, "native_acceptance": False, "heldout_acceptance": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error),
                          "native_acceptance": False}))
        raise SystemExit(3)
