from __future__ import annotations

from base64 import b64encode
import codecs
from copy import deepcopy
import importlib
import json
from math import isclose
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial")]

from DrawingFrontBundleProcess import AUDIT, check_bundle, digest, require
from DrawingFrontDefinitionProcess import inject_probe
from DrawingGraphBridge import generated_document
from PrepareScaledDrawing import prediction
from Classes import registry
from defs.Definition import load_definition
from builders.DrawingFrontBundle import construct_front_bundle
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadFrontDef import ReadFrontDef
from convert.adapters.solidworks.Drawing.Definition.Linked.WriteFrontDef import WriteFrontDef
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef


def named_probe(document, probe):
    model = document.FieldsValue["model"]
    sheet = model.FieldsValue["f1430"]
    view, = [row["o"] for row in sheet.FieldsValue["f60"]["list"]["items"]
             if row["o"].ClassValue.NameValue == "moAbsoluteView"]
    fields = view.FieldsValue
    if probe == "selector":
        fields["f1010"] = 9
    elif probe == "basis":
        if fields["f1018"] == "*Front":
            fields["f5e0"]["has_matrix"] = 1
        else:
            fields["f5e0"]["f08"]["m0"] += 0.125
    elif probe == "eligibility":
        fields["f610"] ^= 48
    elif probe == "scale_zero":
        fields["f780"] = 0.0
    elif probe == "scale_negative":
        fields["f780"] = -0.5
    elif probe == "scale_boolean":
        fields["f780"] = True
    elif probe == "scale_nonfinite":
        fields["f780"] = float("inf")
    elif probe == "scale_underflow":
        fields.update(f780=1e-310, f788=1e100)
    elif probe == "scale_overflow":
        fields.update(f780=1e308, f788=1e-308)
    elif probe == "scale_frame":
        fields["f5e0"]["f70"] *= 2
    elif probe == "inherited_scale":
        fields["f610"] = (fields["f610"] & ~8) | (1 << 26)
    elif probe not in ("family_mismatch", "unsupported_family", "read_family"):
        inject_probe(document, probe)


def compare_prediction(request, inspection, document):
    predicted = prediction(request)
    expected = predicted["expected"]["view"]
    require(predicted["corner_count"] == 8, "named drawing prediction lost an independent prism corner")
    require(all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
                for left, right in zip(inspection["outline_m"], expected["outline_m"], strict=True)),
            "named drawing independent projected corner outline differs")
    model = document.FieldsValue["model"]
    sheet = model.FieldsValue["f1430"]
    view, = [row["o"] for row in sheet.FieldsValue["f60"]["list"]["items"]
             if row["o"].ClassValue.NameValue == "moAbsoluteView"]
    frame = view.FieldsValue["f5e0"]
    raw = expected["model_to_view"]
    matrix = (tuple(frame["f08"][f"m{index}"] for index in range(9)) if frame["has_matrix"]
              else (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
    actual = (*matrix, *(frame[key] for key in ("f58", "f60", "f68")), frame["f70"], 0.0, 0.0, 0.0)
    require(all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
                for left, right in zip(actual, raw, strict=True)),
            "named drawing independent canonical frame differs")
    return {"independent_corner_count": predicted["corner_count"], "independent_outline_m": expected["outline_m"],
            "independent_raw_outline_m": predicted["raw_outline_m"],
            "independent_canonical_frame": True, "independent_corner_projection": True}


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-named-definition-process.v1", "named drawing Definition job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    require(not callable(getattr(SldprtAdapter(), "write", None)), "named drawing Definition enabled the public adapter")
    rules = registry()
    independent_rules = registry()
    AUDIT.BeginBuild()
    request = job["request"]
    canonical = construct_front_bundle(registry=rules, request=deepcopy(request))
    independent = construct_front_bundle(registry=independent_rules, request=deepcopy(request))
    document = generated_document(construction=SimpleNamespace(model=independent.view["owner"]["owner"]),
                                  request=request["drawing"])
    probe = job.get("qualification_probe")
    named_probe(document, probe)
    orientation = job["orientation"]
    alternate = "*Top" if orientation == "*Front" else "*Front"
    if probe == "family_mismatch":
        orientation = alternate
    if probe == "unsupported_family":
        orientation = "*Dimetric"
    version = 18000 if probe == "archive_version" else 19000
    output = WriteNamedDef(NamedGraph(document, version, orientation))
    require(output.OutputValue == canonical.streams["Contents/Definition"], "SDK named drawing Definition changed generated bytes")
    require(output.MapValue.CounterValue == canonical.definition_map_count, "SDK named drawing Definition map differs")
    sdk_read = ReadNamedDef(output.OutputValue, 19000, orientation)
    sdk_again = WriteNamedDef(sdk_read.GraphValue)
    require(sdk_again.OutputValue == output.OutputValue
            and sdk_read.MapValue.CounterValue == output.MapValue.CounterValue
            and sdk_again.MapValue.CounterValue == output.MapValue.CounterValue,
            "SDK named drawing Definition complete read and reemission differs")
    if probe in ("read_tail", "read_version", "read_family"):
        ReadNamedDef(output.OutputValue + (b"\0" if probe == "read_tail" else b""),
                     18000 if probe == "read_version" else 19000, alternate if probe == "read_family" else orientation)
        raise ValueError("named drawing Definition accepted an unqualified reader input")
    expect_front = orientation == "*Front" and request["view"]["scale"] == 1.0
    for action, argument in ((WriteFrontDef, FrontGraph(document, 19000)), (ReadFrontDef, output.OutputValue)):
        try:
            action(argument, 19000) if action is ReadFrontDef else action(argument)
        except (BodyUnsupported, ValueError):
            require(not expect_front, "named drawing Definition changed original front admission")
        else:
            require(expect_front, "named drawing Definition silently widened original front admission")
    streams = dict(independent.streams)
    streams["Contents/Definition"] = output.OutputValue
    require(streams == canonical.streams, "SDK named drawing Definition changed another logical stream")
    parsed, archive = load_definition(output.OutputValue, rules, 19000)
    require(archive.left() == 0 and not parsed.tail and archive.count == output.MapValue.CounterValue,
            "SDK named drawing Definition has incomplete independent readback")
    payload = build_sldprt(streams)
    part_data = build_sldprt(independent.part.streams)
    inspection = check_bundle(drawing_data=payload, part_data=part_data, bundle=independent, request=request, rules=rules)
    independent_geometry = compare_prediction(request, inspection, document)
    require(not AUDIT.DeniedReads, "named drawing Definition attempted runtime input access")
    usage = GetBodyReport(output.UsageValue)
    require(usage["completed"] and not usage["missing_schemas"], "named drawing Definition grammar did not finish")
    result = {"schema": "kit.sw2026.sdk-named-definition-result.v1", "passed": True,
              "orientation": orientation, "view_scale": request["view"]["scale"],
              "definition_bytes": len(output.OutputValue), "definition_sha256": digest(output.OutputValue),
              "definition_map_next_index": output.MapValue.CounterValue,
              "all_logical_streams_identical": True, "artifact_bytes": len(payload), "artifact_sha256": digest(payload),
              "artifact_base64": b64encode(payload).decode("ascii"), "child_artifact_sha256": digest(part_data),
              "usage": usage, "inspection": inspection, **independent_geometry,
              "complete_sdk_readback": True, "sdk_read_write_identical": True,
              "complete_research_readback": True, "public_reader_passed": True,
              "front_profile_unchanged": True, "runtime_input_file_access_attempts": len(AUDIT.DeniedReads),
              "heldout_inputs_read": 0, "vendor_runtime_executed": False, "native_acceptance": False,
              "public_writer_enabled": False, "research_semantic_factory_retained": True}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("named drawing Definition rejected: " + str(error)) from error
