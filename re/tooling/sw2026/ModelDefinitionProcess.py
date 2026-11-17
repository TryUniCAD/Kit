from __future__ import annotations

from base64 import b64decode, b64encode
import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from builders.Definition import assembly_definition, definition_stream, part_definition
from convert.adapters.solidworks.Archive.Definition.Construction.MakeAssemblyDef import MakeAssemblyDef
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))


def inspect(data, version):
    restored = ReadModelDef(data, version)
    wire = WriteModelDef(restored.GraphValue)
    if wire.OutputValue != data or wire.MapValue.CounterValue != restored.MapValue.CounterValue:
        raise ValueError("typed model Definition coordinate or map changed")
    if not (wire.UsageValue.IsComplete and restored.UsageValue.IsComplete):
        raise ValueError("typed model Definition was not fully consumed")
    doc = restored.GraphValue.DocumentValue
    fields = doc.FieldsValue
    journal = fields["ffd8"]["f18"]
    return {
        "document_class": doc.ClassValue.NameValue, "next_map_index": wire.MapValue.CounterValue,
        "journal_schema": journal.ClassValue.SchemaValue, "journal_name": journal.FieldsValue["f08"],
        "density_kg_m3": fields.get("f1688"), "save_as_part": fields.get("f1b48"),
        "style_count": len(fields["f878"]["styles"]), "font_count": len(fields["f870"].FieldsValue["f10"]),
        "view_environment_count": len(fields["faf8"]), "has_material_state": bool(fields["has_pwmaterial"]),
        "display_flags": [fields["fad8_0"], fields["fad8_1"]], "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def generate(job):
    presentation = job["presentation"]
    copied = presentation | {"tessellation": tuple(presentation["tessellation"])}
    settings = ModelDefSettings(
        copied["drafting_standard"], tuple(copied["detail_flags"]), copied["tessellation"],
        copied["system_preference_7a"], copied["journal_name"], job["version"],
    )
    if job["kind"] == "part":
        graph = MakePartDef(settings, job["density_kg_m3"])
        independent = part_definition(density_kg_m3=job["density_kg_m3"], **copied)
    elif job["kind"] == "assembly":
        graph = MakeAssemblyDef(settings, job["save_as_part_preferences"])
        independent = assembly_definition(save_as_part_preferences=job["save_as_part_preferences"], **copied)
    else:
        raise ValueError("unsupported model Definition class")
    wire = WriteModelDef(graph)
    if wire.OutputValue != definition_stream(registry=REGISTRY, document=independent):
        raise ValueError("fresh typed Definition differs from independent field serialization")
    result = inspect(wire.OutputValue, job["version"])
    return result | {"output": b64encode(wire.OutputValue).decode("ascii"), "independent_wire_equal": True}


def run(job):
    reads_before = len(AUDIT.DeniedReads)
    try:
        if job["mode"] == "build":
            result = generate(job)
        elif job["mode"] == "prepare":
            result = inspect(b64decode(job["input"], validate=True), job["version"])
        else:
            raise ValueError("unsupported proof stage")
        result["passed"] = True
    except (ValueError, TypeError, KeyError) as error:
        result = {"passed": False, "error": str(error)}
    result["runtime_input_reads"] = len(AUDIT.DeniedReads) - reads_before
    return result


if __name__ == "__main__":
    jobs = json.load(sys.stdin)
    if AUDIT.DeniedReads:
        raise RuntimeError("definition initialization attempted a forbidden runtime read")
    AUDIT.BeginBuild()
    print(json.dumps([run(job) for job in jobs], allow_nan=False, sort_keys=True))
