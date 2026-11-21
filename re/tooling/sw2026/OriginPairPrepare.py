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
from OriginPairChecks import check_display, require
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef


def main():
    result = json.load(sys.stdin)
    require(result["schema"] == "kit.sw2026.sdk-origin-drawing-result.v1" and result["passed"] is True,
            "origin preparation requires a complete successful generation result")
    drawings, child_bytes = b64decode(result["drawing_base64"], validate=True), b64decode(result["child_base64"], validate=True)
    require(sha256(drawings).hexdigest() == result["drawing_sha256"] and len(drawings) == result["drawing_bytes"]
            and sha256(child_bytes).hexdigest() == result["child_sha256"] and len(child_bytes) == result["child_bytes"],
            "origin preparation artifact custody differs")
    archive = SldprtArchive.from_bytes(drawings)
    child_archive = SldprtArchive.from_bytes(child_bytes)
    loaded = ReadNamedDef(archive.require("Contents/Definition"), 19000, result["orientation"])
    child = ReadNativeLink(child_archive, 0)
    require(WriteNamedDef(loaded.GraphValue).OutputValue == archive.require("Contents/Definition"), "prepared origin Definition changed bytes")
    profile = check_display(loaded.GraphValue, child.ResolvedValue.RootsValue, child.ConfigValue.HeaderValue)
    require(profile == result["profile"], "independent origin pair decode differs from its constructed graph")
    shape = inspect_child(child.ResolvedValue.RootsValue, result["child_shape"]["anchor_kind"])
    require(shape == result["child_shape"], "independent child anchor geometry differs")
    source_header = child.ConfigValue.HeaderValue
    logs = ReadLogItems(source_header.FieldsValue.get("f20"), "moLogs_c")
    matching_logs = tuple(value for value in logs if value.FieldsValue["f48"] == profile["child_origin_id"])
    return {"schema": "kit.sw2026.sdk-origin-drawing-preparation.v1", "passed": True,
            "drawing_sha256": result["drawing_sha256"], "child_sha256": result["child_sha256"],
            "complete_definition_byte_identity": True, "typed_linked_child_complete": True,
            "profile": profile, "child_shape": shape, "origin_creation_log_count": len(matching_logs),
            "datum_time_is_native_unset_when_no_creation_event": not matching_logs,
            "unprojected": list(loaded.Unprojected),
            "config_map_next": child.ConfigValue.MapValue.CounterValue,
            "resolved_map_next": child.ResolvedValue.MapValue.CounterValue,
            "native_acceptance": False, "heldout_acceptance": False, "public_drawing_writer_enabled": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error), "native_acceptance": False}))
        raise SystemExit(3)
