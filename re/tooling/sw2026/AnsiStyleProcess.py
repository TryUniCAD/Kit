from __future__ import annotations

from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
sys.path.append(str(ROOT / "re/tooling/sw2026"))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from ansi_style.Codec import context, decode, encode, field_diff, plain
from ansi_style.Observe import ansi_rules
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.MakeAnsiDetails import (
    MakeAnsiDetails,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeDetails import (
    MakeDetails,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def build():
    if set(REQUEST) != {"case", "styles", "mode", "version"}:
        raise ValueError("ANSI style request has unexpected fields")
    context(REQUEST["version"])
    values = dict(REQUEST["styles"])
    if set(values) != set(StyleInput.__dataclass_fields__):
        raise ValueError(
            "ANSI style input is incomplete or contains unsupported fields"
        )
    for key in ("PrintWidths", "ExclusionNames", "TaskLabels", "CutlistExpressions"):
        if not isinstance(values[key], list):
            raise TypeError("style arrays must be explicit JSON lists")
        values[key] = tuple(values[key])
    settings = StyleInput(**values)
    if REQUEST["mode"] == "ansi":
        fields = MakeAnsiDetails(settings)
    elif REQUEST["mode"] == "iso" and settings.StandardValue == 1:
        fields = MakeDetails(**values)
    else:
        raise ValueError("style mode and explicit standard disagree")
    data, written = encode(ArchiveNode(RuntimeClass("moDetailDefs_c", 1), fields))
    decoded, reader, scope = decode(data)
    reemitted, rewritten = encode(decoded)
    if (
        reemitted != data
        or reader.MapValue.CounterValue != written.MapValue.CounterValue
    ):
        raise ValueError("complete typed style bytes or map identities changed")
    if REQUEST["mode"] == "ansi":
        ansi_rules(decoded.FieldsValue)
    return {
        "case": REQUEST["case"],
        "mode": REQUEST["mode"],
        "qualified": True,
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
        "reencoded_sha256": sha256(reemitted).hexdigest(),
        "tail": reader.Cursor.GetRemaining(),
        "map_counter": reader.MapValue.CounterValue,
        "used_schemas": sorted(scope.UsageValue.SchemaCalls),
        "missing_schemas": sorted(scope.UsageValue.MissingNames),
        "fields": plain(decoded.FieldsValue),
        "native_acceptance": False,
        "full_source_admission": False,
    }


try:
    RESULT = build()
except (TypeError, ValueError, KeyError, PermissionError) as error:
    RESULT = {
        "case": REQUEST.get("case"),
        "qualified": False,
        "diagnostic": str(error),
        "error_type": type(error).__name__,
    }
RESULT["runtime_input_reads"] = len(AUDIT.DeniedReads)
RESULT["runtime_research_imports"] = sorted(
    name
    for name in sys.modules
    if name == "builders"
    or name.startswith("builders.")
    or name in ("Core", "Classes", "Streams", "Schema")
)
print(json.dumps(RESULT, sort_keys=True, ensure_ascii=False, allow_nan=False))
raise SystemExit(
    0
    if RESULT["qualified"]
    and not AUDIT.DeniedReads
    and not RESULT["runtime_research_imports"]
    else 1
)
