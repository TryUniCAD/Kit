# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import math
import os
import sys
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Native.FixedPrism.ReadFixAnchor import ReadFixAnchor
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField, SameNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadRectAxes import ReadRectAxes
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import CheckPrismFrame
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.Formats.Fusion.DocumentCodec.Materials.ProjectMaterial import ProjectMaterial
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import BindMaterials
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import ResolveMatAsset
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "automation"))
from EncoderRoundTrip.Fusion import generate_candidate

AXES = ("width", "depth", "height")
DEFAULT_WRITTEN_AT = 1795564800
LOGICAL_FILENAME = "semantic.f3d"
REQUEST_LIMIT = 65536


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def exact_fields(value, required, label):
    require(type(value) is dict, f"{label} must be a JSON object")
    missing, extra = set(required) - value.keys(), value.keys() - set(required)
    require(
        not (missing or extra),
        f"{label} fields differ: missing {sorted(missing)}, unsupported {sorted(extra)}",
    )
    return value


def label(value, path):
    require(
        type(value) is str and value.strip() and len(value) <= 1024 and "\0" not in value,
        f"{path} requires a nonempty name of at most 1024 characters",
    )
    value.encode("utf-8")
    return value


def number(value, path):
    require(type(value) in (float, int), f"{path} must be a finite JSON number")
    converted = float(value)
    require(math.isfinite(converted), f"{path} must be a finite JSON number")
    return converted


def read_request(path):
    with path.open("rb") as stream:
        raw = stream.read(REQUEST_LIMIT + 1)
    require(len(raw) <= REQUEST_LIMIT, "Semantic request exceeds 64 KiB")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=json_object), sha256(raw).hexdigest()


def request_spec(request):
    top = exact_fields(
        request, ("schema", "title", "dimensions_mm", "drivers", "names", "material"), "request"
    )
    require(type(top["schema"]) is int and top["schema"] == 1, "Unsupported semantic request schema")
    sizes = exact_fields(top["dimensions_mm"], AXES, "dimensions_mm")
    drivers = exact_fields(top["drivers"], AXES, "drivers")
    names = exact_fields(top["names"], ("sketch", "extrude", "body"), "names")
    material = exact_fields(top["material"], ("label", "density_kg_m3", "rgba"), "material")
    width, depth, height = (number(sizes[axis], f"dimensions_mm.{axis}") for axis in AXES)
    require(min(width, depth, height) > 0, "Cuboid dimensions must be positive")
    rgba = material["rgba"]
    require(type(rgba) is list and len(rgba) == 4, "material.rgba requires four normalized channels")
    channels = [number(value, "material.rgba channel") for value in rgba]
    require(all(0 <= value <= 1 for value in channels), "material.rgba channels must be between zero and one")
    density = number(material["density_kg_m3"], "material.density_kg_m3")
    return DocumentSpec(
        label(top["title"], "title"),
        label(drivers["height"], "drivers.height"),
        height,
        ProfileKind="cuboid",
        WidthMm=width,
        DepthMm=depth,
        ConstrainRectangle=True,
        WidthParamName=label(drivers["width"], "drivers.width"),
        DepthParamName=label(drivers["depth"], "drivers.depth"),
        SketchName=label(names["sketch"], "names.sketch"),
        ExtrusionName=label(names["extrude"], "names.extrude"),
        BodyName=label(names["body"], "names.body"),
        Material=MaterialSpec(label(material["label"], "material.label"), density, ColorValue(*channels)),
    )


def resolved_driver(graph, slot, owner, driver, amount):
    model = ResolveField(graph, slot, "parameter", "Parameter")
    require(
        graph.Resolve(model.Fields["dcParameter"]) == slot
        and model.Fields["isUserDefined"] is False
        and model.Fields["expression"] == driver.Fields["userName"]
        and model.Fields["unit"] == "mm"
        and graph.Resolve(slot.Fields["rrOwnerFeature"])
        == graph.Resolve(slot.Fields["rParentFeature"])
        == owner,
        "Native parameter binding lacks a direct reciprocal owner and driver",
    )
    require(
        driver.Fields["dcParameter"] is None
        and driver.Fields["unit"] == "mm"
        and driver.Fields["expression"] == f"{amount} mm"
        and NumberValue(driver.Fields["value"])
        == NumberValue(model.Fields["value"])
        == NumberValue(slot.Fields["value"])
        == amount / 10,
        "Native distance slot disagrees with its requested driving literal",
    )
    return model.Fields["userName"]


def check_geometry(graph, context, model, spec):
    require(
        ReadExtentMode(context.Extrude) == "one_sided" and NumberValue(context.Taper.Fields["value"]) == 0,
        "Native extrusion is not one-sided and straight",
    )
    lines = OrderLines(graph, graph.ByClass("Line3D"))
    anchor, origin = ReadFixAnchor(graph, lines)
    rules = LinkedNodes(graph, context.Sketch, "constraints")
    dimensions = LinkedNodes(graph, context.Sketch, "dimensions")
    SameNodes(rules, graph.ByClass("SketchGeomConstraint"))
    SameNodes(dimensions, graph.ByClass("FusionSketchLinearDim"))
    ReadRectAxes(graph, context, rules, None, lines)
    indexed = {dim.Fields["constraintType"]: dim for dim in dimensions}
    require(
        len(dimensions) == 2 and indexed.keys() == {1 << 22, 1 << 23},
        "Expected exactly two direct axis dimensions",
    )
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    users = [
        param for param in LinkedNodes(graph, table, "children") if param.Fields["isUserDefined"] is True
    ]
    drivers = {param.Fields["userName"]: param for param in users}
    require(
        len(users) == 3 and drivers.keys() == {spec.WidthParamName, spec.DepthParamName, spec.ParamName},
        "Native parameter table lacks the three independent drivers",
    )
    model_names = {}
    for axis, key, name, amount, side, anchor_index in (
        ("width", 1 << 22, spec.WidthParamName, spec.WidthMm, lines[0], 0),
        ("depth", 1 << 23, spec.DepthParamName, spec.DepthMm, lines[3], 1),
    ):
        dimension = indexed[key]
        operands = LinkedNodes(graph, dimension, "geometries")
        require(
            operands == tuple(graph.Resolve(side.Fields[key]) for key in ("rStartPoint", "rEndPoint"))
            and operands[anchor_index] == anchor
            and graph.Resolve(dimension.Fields["ParentNode"]) == context.Sketch,
            "Native dimension does not constrain the correct anchored side",
        )
        slot = ResolveField(graph, dimension, "dcParameter", "DcDoubleParameter")
        model_names[axis] = resolved_driver(graph, slot, context.SketchFeature, drivers[name], amount)
    model_names["height"] = resolved_driver(
        graph, context.Along, context.Extrude, drivers[spec.ParamName], spec.LengthMm
    )
    require(
        len(model.Bodies) == 1 and isinstance(model.Bodies[0].History, PrismHistory),
        "Expected one typed prism history",
    )
    history = model.Bodies[0].History
    CheckPrismFrame(history.Model, history.Frame)
    native_dimensions = (spec.WidthMm / 10, spec.DepthMm / 10, spec.LengthMm / 10)
    require(
        {point for point in history.Frame.CornersCm}
        == {
            (x, y, z)
            for x in (0, native_dimensions[0])
            for y in (0, native_dimensions[1])
            for z in (0, native_dimensions[2])
        },
        "Native prism frame corners disagree with the requested cuboid",
    )
    return {
        "fixed_corner": anchor.Identity,
        "distinct_fixed_origin": origin.Identity,
        "orientation_rule_count": len(rules),
        "driving_sketch_dimension_count": len(dimensions),
        "model_parameter_names": model_names,
        "extent": "one_sided_positive_z",
        "native_dimensions_cm": dict(zip(AXES, native_dimensions, strict=True)),
        "analytic_volume_mm3": math.prod(native_dimensions) * 1000,
        "analytic_centroid_mm": [value * 5 for value in native_dimensions],
    }


def check_material(graph, body, model, spec):
    packages = BindMaterials(model)
    linked = []
    for key, role in (("physicalMaterial", "physicalmaterial"), ("visualMaterial", "materialappearance")):
        binding = ObjectFields(body.Fields[key])
        manager = graph.Resolve(binding["ProteinAssetManager"])
        require(
            manager.ClassName == "ProteinAssetManager" and manager.ObjectId in packages,
            "Body material is not linked to the native package",
        )
        package = packages[manager.ObjectId]
        asset = ResolveMatAsset(package, binding["assetReference"])
        require(
            asset is not None and asset.AssetRole == role, "Native material binding has the wrong asset role"
        )
        linked.append((package, asset))
    (package, physical), (appearance_package, appearance) = linked
    aspects = [prop.Connections for prop in physical.Properties if prop.FieldName == "physmat_aspects"]
    require(
        package is appearance_package
        and len(aspects) == 1
        and aspects[0] is not None
        and aspects[0].Enabled
        and appearance.InstanceId in aspects[0].Targets,
        "Body appearance does not resolve to the physical material's appearance aspect",
    )
    observed = ProjectMaterial(package, physical.InstanceId)
    requested = spec.Material
    require(
        (observed.NameValue, observed.Density, observed.Color)
        == (requested.NameValue, requested.Density, requested.Color),
        "Linked material label, density or RGBA differs from the semantic request",
    )


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    spec = request_spec(request)
    payload = generate_candidate(MakeFusionDoc(spec), native_locator=LOGICAL_FILENAME, written_at=written_at)
    model = ReadDocument(payload)
    require(
        not model.Configurations and not model.Snapshots and model.Graphics is None,
        "Generated candidate left the archive-free constructor profile",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    require(
        (
            context.Component.Fields["userName"],
            context.Sketch.Fields["userName"],
            context.Extrude.Fields["featureUserName"],
            context.BodyNode.Fields["userName"],
        )
        == (spec.Title, spec.SketchName, spec.ExtrusionName, spec.BodyName),
        "Native object names differ from the request",
    )
    geometry = check_geometry(graph, context, model, spec)
    check_material(graph, context.BodyNode, model, spec)
    return payload, {
        "schema": 1,
        "candidate_sha256": sha256(payload).hexdigest(),
        "candidate_bytes": len(payload),
        "written_at": written_at,
        "source_free_constructor": True,
        "whole_saved_source_admission": False,
        "strict_public_readback": True,
        "vendor_loadable": False,
        "application_usable": False,
        "native_acceptance": "unmeasured",
        "semantics": request,
        "native_checks": {**geometry, "linked_generic_material": True},
        "unsupported_semantics": [
            "procedural_material_mapping",
            "native_saved_display_state",
            "preserved_source_graph",
            "native_saved_snapshot",
            "native_saved_configuration_parts",
            "native_saved_previews",
        ],
        "presentation_scope": "source_free_constructor_without_native_saved_display_snapshot_configuration_or_preview_state",
    }


def publish(destination, payload):
    temporary = None
    try:
        with NamedTemporaryFile(
            dir=destination.parent, prefix=".kit-fusion-semantic-", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        if os.name == "nt":
            os.rename(temporary, destination)
            temporary = None
        else:
            os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a source-free Fusion fixed-corner cuboid research candidate"
    )
    parser.add_argument("request", type=Path, help="version 1 semantic JSON input")
    parser.add_argument("output", type=Path, help="new .f3d destination")
    parser.add_argument(
        "--written-at", type=int, default=DEFAULT_WRITTEN_AT, help="deterministic Unix-second timestamp"
    )
    args = parser.parse_args()
    try:
        require(args.output.suffix.lower() == ".f3d", "Output path must end in .f3d")
        require(
            not args.output.exists() and not args.output.is_symlink(), "Output destination already exists"
        )
        request, request_hash = read_request(args.request)
        payload, report = build(request, written_at=args.written_at)
        receipt = (
            json.dumps({**report, "request_sha256": request_hash}, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
        publish(args.output, payload)
        sys.stdout.buffer.write(receipt)
    except (OSError, KeyError, TypeError, ValueError, OverflowError, RuntimeError) as error:
        parser.exit(1, f"Fusion semantic generation refused: {error}\n")


if __name__ == "__main__":
    main()
