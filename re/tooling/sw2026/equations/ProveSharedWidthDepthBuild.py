from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
MANAGED = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
CASES = {
    "same_locator": (
        "WidthDepthSameLocator02/Neutral.json",
        "2e0a84ca6f061d9c34622ba98a8a440a8322cf55ec8cc2d72b720da0b223c94f",
        "214935d57e37c22eee826ccdb20625a3038560b171e4d0e2abf63a83fd1cc9b8",
    ),
    "distinct_profile": (
        "WidthDepthFresh01/EquationDepthBeta.json",
        "3b17a8c1088782a848325ae985c427744585168a90018977506039f7a19c4cf3",
        None,
    ),
}
FAULTS = {
    "height_identity": "actual width divided by two",
    "different_divisor": "actual width divided by two",
    "independent_depth": "actual width divided by two",
    "source_language": "actual width divided by two",
    "missing_anchor": "explicit Front Plane corner anchor",
    "inconsistent_depth": "disagrees with the anchored Front Plane boss",
}
CONSTRUCTION = Path("src/convert/adapters/solidworks/Archive/Construction")
WRITER_PATHS = tuple(
    CONSTRUCTION / name
    for name in (
        "BodyNames/MakeAnchorBase.py",
        "Dimensions/MakeObList.py",
        "Part/EmitPartArchive.py",
        "Part/EmitPartStreams.py",
        "Part/Equations/BindWidthMut.py",
        "Part/Equations/MakeEqDimension.py",
        "Part/Equations/MakeEqToken.py",
        "Part/Equations/MakeDerivedBoss.py",
        "Part/Equations/PlanWidthDepth.py",
        "Part/FinishBlindMut.py",
        "RectangleAnchors/MakeAnchorPart.py",
    )
)


def digest(data):
    return sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def setup():
    sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent), str(HERE.parent.parent)]


def make_candidate(request, fault):
    from BuildWidthDepthPart import FromData, input_value, settings
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import AnchorPartInput
    from convert.adapters.solidworks.Archive.Construction.Part.Equations.MakeDerivedBoss import MakeDerivedBoss
    from interchange import Expression, ParameterRole
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    document = FromData(request["document"])
    profile, feature = document.sketches[0], document.feature_timeline[0]
    width, height = profile.parameter_ids
    depth, = feature.parameter_ids
    equation = request["equation"]
    require(
        equation == {"target": depth, "dependency": width, "divisor": 2},
        "disclosed author input is missing its explicit typed equation",
    )
    dependency = height if fault == "height_identity" else width
    divisor = 3 if fault == "different_divisor" else equation["divisor"]
    language = "kit" if fault == "source_language" else "solidworks"
    relation = Expression(f'"D1@{profile.name}" / {divisor}', (dependency,), language)
    old_depth = next(value for value in document.parameters if value.id == depth)
    effective_depth = old_depth.value
    if fault == "inconsistent_depth":
        effective_depth = replace(effective_depth, value=float(effective_depth.value) + 1)
        feature = replace(feature, definition=replace(feature.definition, length=effective_depth))
    depth_parameter = replace(
        old_depth,
        value=effective_depth,
        role=ParameterRole.KDriving if fault == "independent_depth" else ParameterRole.KDerived,
        expression=None if fault == "independent_depth" else relation,
    )
    neutral = replace(
        document,
        parameters=tuple(depth_parameter if param is old_depth else param for param in document.parameters),
        feature_timeline=(feature,),
    )
    recipe = settings(request["settings"])
    anchor = AnchorPartInput(
        "center" if fault == "missing_anchor" else "corner",
        input_value(request["rectangle_dimensions"], recipe),
    )
    try:
        part = MakeDerivedBoss(neutral, recipe, anchor)
    except (TypeError, ValueError, KeyError) as error:
        require(fault in FAULTS and FAULTS[fault] in str(error), f"unexpected writer refusal {error}")
        return b"", {"fault": fault, "refusal": str(error), "runtime_input_reads": len(audit.DeniedReads)}
    require(fault is None, "a malformed equation emitted a complete archive")
    report = {
        "runtime_input_reads": len(audit.DeniedReads),
        "map_counters": (part.ConfigValue.MapValue.CounterValue, part.ResolvedValue.MapValue.CounterValue),
        "streams": {name: {"size": len(raw), "sha256": digest(raw)} for name, raw in sorted(part.StreamsValue.items())},
    }
    return part.BytesValue, report


def run_worker(request, fault=None):
    flags = ("--fault", fault) if fault is not None else ()
    response = subprocess.run(
        [sys.executable, "-I", "-B", str(HERE), "--worker", *flags],
        input=request,
        capture_output=True,
        timeout=60,
        check=False,
    )
    require(response.returncode == 0, response.stderr.decode(errors="replace"))
    report = json.loads(response.stderr)
    require(report["runtime_input_reads"] == 0, "construction accessed a runtime file")
    return response.stdout, report


def selected_case(source, values):
    from BuildWidthDepthPart import compose
    from convert import open_document

    name, input_hash, frozen_hash = values
    request = (source / name).read_bytes()
    require(digest(request) == input_hash, "disclosed neutral author input changed")
    raw, proof = run_worker(request)
    require((raw, proof) == run_worker(request), "independent build was not reproducible")
    legacy, old = compose(json.loads(request))
    require(raw == legacy, "shared construction differs from the previous explicit equation model")
    if frozen_hash is not None:
        require(digest(raw) == frozen_hash, "native-tested generated bytes changed")
    document = open_document(raw, source_format="solidworks.sldprt")
    width, height, depth = document.parameters
    require(
        depth.role.value == "derived"
        and depth.expression is not None
        and depth.expression.parameter_ids == (width.id,)
        and tuple(proof["map_counters"]) == (old["config_map_final"], old["resolved_map_final"])
        and document.brep is not None
        and len(document.brep.bodies) == 1
        and len(document.brep_payloads) == 0,
        "strict normal readback did not retain the actual part and its dependency",
    )
    return request, {
        "source_sha256": input_hash,
        "generated_sha256": digest(raw),
        "native_tested_container": frozen_hash is not None,
        "byte_identical_to_previous_model": True,
        "width_depth_identity": (width.id, depth.id),
        "dimensions_mm": (width.value.value, height.value.value, depth.value.value),
        **proof,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed-root", type=Path, default=MANAGED)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--fault", choices=tuple(FAULTS))
    args = parser.parse_args()
    setup()
    if args.worker:
        raw, report = make_candidate(json.load(sys.stdin), args.fault)
        sys.stdout.buffer.write(raw)
        print(json.dumps(report, sort_keys=True), file=sys.stderr)
        return
    outcomes = {name: selected_case(args.disclosed_root, values) for name, values in CASES.items()}
    reports = {name: outcome[1] for name, outcome in outcomes.items()}
    sizes = [tuple(item["size"] for item in row["streams"].values()) for row in reports.values()]
    require(len(set(sizes)) == len(CASES), "stream lengths did not follow distinct neutral inputs")
    guards = {}
    for fault in FAULTS:
        output, report = run_worker(outcomes["same_locator"][0], fault)
        require(not output and report["fault"] == fault, "refused input published bytes")
        guards[fault] = report
    result = {
        "schema": "kit.sw2026.shared-width-depth-build.v1",
        "cases": reports,
        "faults": guards,
        "isolated_worker_processes": 2 * len(CASES) + len(FAULTS),
        "native_processes": 0,
        "heldout_inputs_read": False,
        "tool_sha256": digest(HERE.read_bytes()),
        "writer_sha256": {str(path): digest((ROOT / path).read_bytes()) for path in WRITER_PATHS},
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
