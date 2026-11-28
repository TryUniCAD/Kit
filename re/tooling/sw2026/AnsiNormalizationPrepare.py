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

from ansi_pair.Readback import fields
from ansi_normalization.Inspect import inspect_initialization
from ansi_normalization.LinkedState import linked_state
from OriginChildShape import inspect_child
from OriginPairChecks import check_display
from SpatialTextMut import require, text_rows
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)


def main():
    source = json.load(sys.stdin)
    require(
        source["schema"] == "kit.sw2026.ansi-normalization-result.v1"
        and source["passed"] is True,
        "ANSI preparation requires a complete independently generated pair",
    )
    data = {
        name: b64decode(source[name + "_base64"], validate=True)
        for name in ("child", "drawing")
    }
    for name, raw in data.items():
        require(
            len(raw) == source[name + "_bytes"]
            and sha256(raw).hexdigest() == source[name + "_sha256"],
            "ANSI preparation bytes differ",
        )
        actual = SldprtArchive.from_bytes(raw).streams
        require(
            set(actual) == set(source[name + "_streams"]),
            "ANSI logical stream inventory differs",
        )
        for stream, value in actual.items():
            expected = source[name + "_streams"][stream]
            require(
                sha256(value).hexdigest() == expected["sha256"]
                and len(value) == expected["bytes"]
                and value == b64decode(expected["base64"], validate=True),
                "ANSI logical stream custody differs",
            )
    child, drawing, presentation = fields(
        data["child"], data["drawing"], source["orientation"], source["mode"]
    )
    require(
        source["initialization"] in ("fresh", "document-units"),
        "normalization preparation policy differs",
    )
    if source["initialization"] == "document-units":
        inspect_initialization(
            child.ConfigValue.RootValue, source["presentation"]["child_details"]
        )
        inspect_initialization(
            drawing.GraphValue.DocumentValue.FieldsValue["model"],
            source["presentation"]["drawing_details"],
        )
    require(
        presentation == source["presentation"],
        "ANSI actual typed style graph differs from guarded construction",
    )
    archive = SldprtArchive.from_bytes(data["child"])
    config_data, config = WriteConfigMut(
        child.ConfigValue.RootValue, 19000, child.ConfigValue.HeaderValue
    )
    resolved_data, resolved = WriteResolMut(
        child.ResolvedValue.RootsValue,
        child.ResolvedValue.ExtraFields,
        19000,
        config.MapValue,
        child.ResolvedValue.ContextValue,
    )
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    require(
        config_data == archive.require("Contents/Config-0")
        and resolved_data == archive.require("Contents/Config-0-ResolvedFeatures")
        and WriteCmgrMut(manager.RootValue, 19000) == archive.require("Contents/CMgr"),
        "ANSI linked child codec replay differs",
    )
    require(
        WriteNamedDef(drawing.GraphValue).OutputValue
        == SldprtArchive.from_bytes(data["drawing"]).require("Contents/Definition"),
        "ANSI drawing codec replay differs",
    )
    shape = inspect_child(
        child.ResolvedValue.RootsValue, source["child_shape"]["anchor_kind"]
    )
    profile = check_display(
        drawing.GraphValue,
        child.ResolvedValue.RootsValue,
        child.ConfigValue.HeaderValue,
    )
    ordinary = next(
        n
        for n in child.ResolvedValue.RootsValue
        if n.ClassValue.NameValue == "moProfileFeature_c"
    )
    require(
        shape == source["child_shape"]
        and profile == source["profile"]
        and text_rows(ordinary) == source["text_after"],
        "ANSI geometry dimension or origin ownership differs",
    )
    require(
        linked_state(child) == source["linked_state"],
        "independent linked graph and inherited aliases differ",
    )
    return {
        "schema": "kit.sw2026.ansi-normalization-preparation.v1",
        "passed": True,
        "mode": source["mode"],
        "initialization": source["initialization"],
        "presentation": presentation,
        "config_map_next": config.MapValue.CounterValue,
        "linked_state": linked_state(child),
        "resolved_map_next": resolved.MapValue.CounterValue,
        "complete_part_definition": True,
        "complete_config": True,
        "complete_resolved": True,
        "complete_cmgr": True,
        "complete_drawing_definition": True,
        "actual_origin_aliases": True,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "exception": type(error).__name__,
                    "diagnostic": str(error),
                    "native_acceptance": False,
                }
            )
        )
        raise SystemExit(3)
