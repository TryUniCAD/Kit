from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
PACKET = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover/WidthDepthSameLocator04")
NEUTRAL = "90d9d22d737bd8d313a68d10eef1e3cb730bdae81c973a3656b591d627ad786b"
NATIVE = "b544ff3d3668f7dc9815bd862b6d1f067174503cd310e4a7cff56ce8d8458ba2"
EXPECTED = "5783b3944d76563ae8143b8789a923f1b07fb4eb94f4b59fef50b6b80ac696b6"
FAULTS = ("missing_coincidence", "wrong_corner", "height_dependency", "unavailable_configuration", "unmodeled_metadata")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def write_scoped(request, fault):
    sys.path[:0] = list(map(str, (HERE.parent, HERE.parent.parent, ROOT / "src", ROOT)))
    from BuildSdkWidthDepth import author_document
    from convert import open_document, write_document
    from convert.adapters.registry import AdapterNotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.Enums.EnumDocument import Capability
    from interchange.geometry.Models.Sketch import ConstraintRef
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    doc = author_document(request)
    doc = replace(doc, capabilities=doc.capabilities | {Capability.KExpressions})
    sketch, = doc.sketches
    configuration = doc.configurations[0].name
    if fault == "missing_coincidence":
        doc = replace(doc, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),))
    if fault == "wrong_corner":
        anchor = sketch.constraints[-1]
        second = ConstraintRef(sketch.closed_profile_entity_ids[0][1], "start")
        moved = replace(anchor, references=(anchor.references[0], second))
        doc = replace(doc, sketches=(replace(sketch, constraints=(*sketch.constraints[:-1], moved)),))
    if fault == "height_dependency":
        role = doc.feature_timeline[0].parameter_ids[0]
        doc = replace(doc, parameters=tuple(
            replace(row, expression=replace(row.expression, parameter_ids=(sketch.parameter_ids[1],)))
            if row.id == role else row for row in doc.parameters))
    if fault == "unavailable_configuration":
        configuration = "unavailable"
    if fault == "unmodeled_metadata":
        doc = replace(doc, metadata={**doc.metadata, "unmodeled": True})

    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    import_module("interchange.document.Models.DocumentProvenance")
    import_module("interchange.document.Behavior.DocumentIo")
    import_module("interchange.brep.Validation.BrepValidate")
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: request["sdk_created_at"]
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    target = BytesIO()
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    support = SldprtWriter().supports(doc, target)
    require(support == (fault in (None, "unavailable_configuration")), "writer selection did not enforce model admission")
    try:
        result = write_document(
            doc, target, destination_format="solidworks.sldprt", configuration=configuration,
            allow_carrier=False, values={
                "final_destination": request["settings"]["output"]["path_name"],
                "require_native_transfers": True,
            },
        )
    except (AdapterNotFoundError, ValueError, TypeError) as error:
        require(fault in FAULTS and not target.getvalue(), "the scoped writer unexpectedly refused or published bytes")
        return {"fault": fault, "supported": support, "status": str(error), "runtime_reads": len(audit.DeniedReads)}
    require(fault is None, "an unsupported intent published a native part")
    raw = target.getvalue()
    require(digest(raw) == EXPECTED and result.bytes_written == len(raw)
            and result.application_usable and result.vendor_loadable
            and Capability.KExpressions in result.native_capabilities,
            "the normal route did not reproduce the exact native-tested bytes and capability")
    decoded = open_document(raw, source_format="solidworks.sldprt")
    width, height, depth = decoded.parameters
    require(decoded.brep is not None and len(decoded.brep.bodies) == 1
            and len(decoded.brep_payloads) == 0 and decoded.configurations[0].name == configuration
            and depth.expression is not None and depth.expression.parameter_ids == (width.id,)
            and depth.value.value == width.value.value / 2.0,
            "normal strict read did not preserve the anchored equation part")
    return {
        "sha256": digest(raw), "bytes": len(raw), "supported": support,
        "equation_parameter_ids": [width.id, depth.id], "lengths_mm": [row.value.value for row in (width, height, depth)],
        "solid_count": len(decoded.brep.bodies), "native_expressions_capability": True,
        "runtime_reads": len(audit.DeniedReads),
    }


def worker(raw, fault=None):
    args = [sys.executable, "-I", "-B", str(HERE), "--worker"]
    if fault is not None:
        args.extend(("--fault", fault))
    process = subprocess.run(args, input=raw, capture_output=True, timeout=60, check=False)
    require(process.returncode == 0, process.stderr.decode(errors="replace"))
    result = json.loads(process.stdout)
    require(result["runtime_reads"] == 0, "normal API path accessed a runtime file")
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, default=PACKET)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--fault", choices=FAULTS)
    options = parser.parse_args()
    if options.worker:
        print(json.dumps(write_scoped(json.load(sys.stdin), options.fault), sort_keys=True, allow_nan=False))
        return
    request = (options.packet / "Neutral.json").read_bytes()
    evidence = (options.packet / "Result.json").read_bytes()
    require(digest(request) == NEUTRAL and digest(evidence) == NATIVE, "the accepted disclosed packet must be exact")
    row = worker(request)
    require(row == worker(request), "normal writer output was not deterministic for the fixed creation event")
    result = {
        "schema": "kit.sw2026.public-width-depth-writer.v1",
        "native_result_sha256": NATIVE, "neutral_input_sha256": NEUTRAL,
        "isolated_worker_processes": 2 + len(FAULTS), "native_processes_started": 0,
        "heldout_inputs_read": 0, "exact_native_tested_output": row,
        "refusals": {fault: worker(request, fault) for fault in FAULTS},
        "writer_sha256": {
            path: digest((ROOT / path).read_bytes())
            for path in (
                "src/convert/adapters/solidworks/Core/Preparation/Equations/PlanEqPart.py",
                "src/convert/adapters/solidworks/Core/Preparation/PlanNativePart.py",
                "src/convert/adapters/solidworks/Core/Preparation/PrepareNative.py",
                "src/convert/adapters/solidworks/Core/Writing/SldprtWriter.py",
                "src/convert/adapters/solidworks/Core/Writing/SldWriteInfo.py",
            )
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
