from codecs import lookup
from hashlib import sha256
from importlib import import_module
from math import isclose
from pathlib import Path
import json
import sys

from SdkBlindPartSettings import settings
from SdkRectDimRejects import input_value
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import MakeSelfComp
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def rows(*nodes):
    return {"n": len(nodes), "items": [{"o": value} for value in nodes]}


def operand(dimension):
    name = ReadNodeName(dimension.ParameterValue)
    feature = ReadNodeName(dimension.HandleValue.FieldsValue["owner"])
    if not all(value.isascii() and value.isprintable() for value in (name, feature)):
        raise ValueError("this equation profile requires printable ASCII dimension owners")
    if any(character in name + feature for character in ('"', "@", "\\")):
        raise ValueError("this equation profile cannot escape dimension owner names")
    return f'"{name}@{feature}"'


def local_dimension_wrapper(root, dimension):
    driver = dimension.HandleValue
    if driver.FieldsValue["f58"] is not None:
        raise ValueError("this equation profile requires a local driver handle")
    reference = ArchiveNode(
        driver.ClassValue, {**driver.FieldsValue, "f58": MakeSelfComp(root)}
    )
    return node(
        "moDimRefWrapper_c",
        {
            "fb0": dimension.ParameterValue.FieldsValue["f58"],
            "f58": reference,
            "f68": 0,
            "f60": None,
            "f6c": 0,
            "f08": 101,
            "has_f10": 0,
            "has_f18": 0,
            "f0c": -1,
            "f20": 0,
            "f74": -12345,
            "f78": -12345,
            "f7c": -12345,
            "f50": 0,
            "f70": driver.FieldsValue["f4c"],
            "f34": 0,
            "f30": 0,
            "f98": 0,
            "f38": -1,
        },
    )


def token(name, text, start, kind, color, **fields):
    return node(
        name,
        {
            **fields,
            "f08": text,
            "f10": color,
            "f14": start,
            "f18": start + len(text),
            "f1c": kind,
        },
    )


def dimension_token(root, dimension, text, start):
    return token(
        "moRelDimension_c", text, start, 0, 1,
        f30=rows(), f78=None, f80=local_dimension_wrapper(root, dimension),
    )


def attach_equation(root, width, depth, divisor):
    manager = root.FieldsValue["f9d0"]
    if manager.FieldsValue["f58"]["n"] != 0:
        raise ValueError("this equation profile requires a fresh part relation manager")
    lhs, dependency, literal = operand(depth), operand(width), str(divisor)
    rhs = f" = {dependency} / {literal}"
    next_id = manager.FieldsValue["ff4"] + 1
    relation = node(
        "moRelation_c",
        {
            "f10": lhs + rhs,
            "f18": 1 << 9,
            "f48": 0,
            "f74": 0,
            "f08": next_id,
            "f38": "uuUNDEFINED",
            "f88": 0,
            "f6c": 0,
            "f8c": 0,
        },
    )
    left_tokens = rows(dimension_token(root, depth, lhs, 0))
    right_tokens = rows(
        token("moRelOperator_c", "=", 0, 3, 8),
        dimension_token(root, width, dependency, 2),
        token("moRelOperator_c", "/", len(dependency) + 3, 3, 8),
        token("moRelValue_c", literal, len(dependency) + 5, 2, 8),
    )
    for field, text, tokens, is_left in (
        ("f58", lhs, left_tokens, 1),
        ("f60", rhs, right_tokens, 0),
    ):
        relation.FieldsValue[field] = node(
            "moRelEquationSide_c",
            {"f10": tokens, "f50": text, "f58": 0, "f98": is_left, "fa0": relation},
        )
    manager.FieldsValue.update(f58=rows(relation), ff4=next_id, f150=1)
    return relation.FieldsValue["f10"]


def compose(request):
    document = FromData(request["document"])
    provision = settings(request["settings"])
    plan = ProjectRectDims(document)
    CheckPartInput(document, provision, plan)
    equation = request["equation"]
    divisor = equation["divisor"]
    if (
        equation["dependency"] != document.sketches[0].parameter_ids[0]
        or equation["target"] != document.feature_timeline[0].parameter_ids[0]
        or type(divisor) is not int
        or divisor != 2
        or not isclose(plan.DepthValue, plan.WidthValue / divisor, rel_tol=1e-12)
    ):
        raise ValueError("the equation must bind the actual width and depth with a factor of two")
    allocator = PersistentIds()
    system = MakePartBaseMut(provision, plan, allocator)
    profile = MakePartProfMut(system, provision, plan, allocator)
    dimensions = MakeRectDimsMut(
        profile, input_value(request["rectangle_dimensions"], provision),
        allocator, plan.SketchDriverNames,
    )
    MakeCornerMut(profile, system.OriginValue)
    part = FinishBlindMut(
        system, profile, provision, plan, allocator,
        MakeSketchKeys(dimensions, provision.DocumentUnits.LengthUnit),
    )
    expression = attach_equation(
        system.RootValue, dimensions[0], part.BossValue.DimensionsValue[0], divisor
    )
    version = part.ConfigValue.VersionValue
    config, config_graph = WriteConfigMut(
        system.RootValue, version, part.HeaderValue, PartRelations=True
    )
    resolved, feature_graph = WriteResolMut(
        part.ResolvedValue.RootsValue, part.ResolvedValue.ExtraFields,
        version, config_graph.MapValue, part.ResolvedValue.ContextValue,
    )
    restored = ReadConfigMut(config, version, part.HeaderValue, PartRelations=True)
    reread = ReadResolvedMut(
        resolved, version, restored.MapValue, part.ResolvedValue.ContextValue
    )
    config_again, reseeded = WriteConfigMut(
        restored.RootValue, version, part.HeaderValue, PartRelations=True
    )
    resolved_again, _ = WriteResolMut(
        reread.RootsValue, reread.ExtraFields, version, reseeded.MapValue, reread.ContextValue
    )
    if config != config_again or resolved != resolved_again:
        raise ValueError("the fresh linked streams did not round-trip")
    streams = {
        **part.StreamsValue,
        "Contents/Config-0": config,
        "Contents/Config-0-ResolvedFeatures": resolved,
    }
    return BuildSldprt(streams, FormatVersion=4), {
        "expression": expression,
        "config_map_final": config_graph.MapValue.CounterValue,
        "resolved_map_final": feature_graph.MapValue.CounterValue,
        "streams": {
            name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
            for name, data in sorted(streams.items())
        },
    }


def main():
    root = Path(__file__).resolve().parents[4]
    request = json.load(sys.stdin)
    for module in (
        "DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"
    ):
        import_module("interchange.document.Validation." + module)
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    output, result = compose(request)
    result.update(
        sha256=sha256(output).hexdigest(), bytes=len(output),
        runtime_input_file_reads=len(audit.DeniedReads),
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False), file=sys.stderr)
    sys.stdout.buffer.write(output)


if __name__ == "__main__":
    main()
