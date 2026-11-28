# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import sys
from dataclasses import fields, replace
from pathlib import Path

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import BindMaterials
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import ResolveMatAsset
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.Formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue

from DesignHeightEvidence import digest, height_parameters, mapped, one, require

ZERO = (0.0, 0.0, 0.0)
IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def load(path, *hashes):
    raw = path.read_bytes()
    require(len(set((digest(raw), *hashes))) == 1, f"Archive digest disagrees with custody for {path.name}")
    return ReadDocument(raw)


def frame_bounds(model):
    history = one(model.Bodies, "body").History
    require(isinstance(history, PrismHistory), "Expected a typed prism history")
    axes = tuple(zip(*history.Frame.CornersCm, strict=True))
    bounds = (*map(min, axes), *map(max, axes))
    require(
        len(bounds) == 6 and bounds[:3] == ZERO and min(bounds[3:]) > 0, "Expected a positive XY cuboid frame"
    )
    return bounds


def entity_ref(node):
    return EntityRef(node.SegmentId, node.ObjectId)


def material(model, graph, body):
    parts = BindMaterials(model)
    part = one(model.Materials, "material package")
    require(
        not mapped(body.Fields["faceVisualMaterialByAttrTagID"]), "Unsupported per-face material assignments"
    )
    bindings = {}
    resolved = {}
    for role, prefix, key in (
        ("physicalmaterial", "PhysicalMaterial", "physicalMaterial"),
        ("materialappearance", "VisualMaterial", "visualMaterial"),
    ):
        binding = ObjectFields(body.Fields[key])
        manager = graph.Resolve(binding["ProteinAssetManager"])
        reference = binding["assetReference"]
        require(
            manager.ClassName == "ProteinAssetManager"
            and parts == {manager.ObjectId: part.Package}
            and part.Name == "ProteinAssets.BlobParts/" + manager.Fields["partName"]
            and SeriesItems(manager.Fields[prefix + "AssetReferences"]) == (reference,)
            and SeriesItems(manager.Fields[prefix + "RefCountVector"]) == (1,),
            "Unbound body material manager",
        )
        effective = ResolveMatAsset(part.Package, reference)
        require(
            effective is not None
            and effective.AssetRole == role
            and effective.DefinitionId == binding["proteinMaterialID"],
            "Unexpected bound material asset",
        )
        bindings[key] = binding
        resolved[key] = effective
    package = part.Package
    assets = {asset.InstanceId: asset for asset in package.Assets}
    phys = resolved["physicalMaterial"]
    visual = resolved["visualMaterial"]
    visual_raw = assets[bindings["visualMaterial"]["assetReference"]]
    link = one(
        [prop for prop in phys.Properties if prop.FieldName == "physmat_aspects"], "physical aspect link"
    )
    require(
        link.Value is None and link.Connections is not None and link.Connections.Enabled,
        "Expected native physical aspect links",
    )
    targets = link.Connections.Targets
    require(
        len(targets) == 2
        and tuple(assets[key].AssetRole for key in targets) == ("Structural", "materialappearance")
        and len({phys.InstanceId, visual.InstanceId, visual_raw.InstanceId, *targets})
        == len(package.Assets)
        == 5,
        "Unsupported physical-aspect or visual alias inventory",
    )
    return part, bindings, (phys, visual_raw, visual, tuple(assets[key] for key in targets))


def mapping(model, graph, body, previous_box):
    layered = ResolveField(graph, body, "textureMapping", "LayeredTextureMapping")
    layers = mapped(layered.Fields["layers"])
    require(
        set(layers) == {2, 3} and layered.Fields["activeLayer"] == 0, "Unsupported texture mapping layers"
    )
    asm, wood = (graph.Resolve(layers[key]) for key in (2, 3))
    require(
        (asm.ClassName, wood.ClassName) == ("ASMTextureMapping", "ProceduralWoodTextureMapping")
        and wood.Fields["originInitilized"] is True,
        "Unsupported procedural texture mapping",
    )
    require(model.Graphics is not None, "Missing body display scene")
    display = one(
        [
            obj
            for obj in model.Graphics.Objects
            if isinstance(obj.Value, GroupValue)
            and isinstance(obj.Value.WorldValue, BrepWorld)
            and (len(obj.Value.WorldValue.EdgeNodes), len(obj.Value.WorldValue.FaceNodes)) == (12, 6)
        ],
        "solid graphics world",
    )
    node = display.Value.NodeData.DataValue
    require(
        isinstance(node, NodeValue)
        and node.EntityLink == entity_ref(body)
        and node.Attributes.NodeRef == display.Reference.ObjectId,
        "Graphics group does not identify the body",
    )
    attr = one(
        [attr for attr in node.Attributes.Attributes if attr.ClassName == "TextureMappingAttribute"],
        "body TextureMappingAttribute",
    )
    field = one(attr.Fields, "texture attribute field")
    texture = field.DataValue
    require(
        field.FieldName == "TextureMapping"
        and isinstance(texture, TextureValue)
        and texture.Reference == entity_ref(layered)
        and texture.Cache.IsLayered
        and texture.Cache.Secondary is not None,
        "Graphics texture does not resolve to the Design mapping",
    )
    require(
        display.Value.WorldValue.ModelBox == previous_box,
        "Aggregate graphics box differs from preceding solved frame",
    )
    for record in (layered, asm, wood):
        bbox = ObjectFields(record.Fields["textureMappingBoundingBox"])
        require(
            (*PointCoords(bbox["min"]), *PointCoords(bbox["max"])) == previous_box,
            "Design texture box differs",
        )
        CheckIdentity(record.Fields["bakedTransformInGeometry"])
        CheckIdentity(record.Fields["textureMappingTransform"])
    for mode, record, cache in ((0, asm, texture.Cache.Primary), (6, wood, texture.Cache.Secondary)):
        require(
            cache.ModeValue == mode
            and cache.AxisValue == PointCoords(record.Fields["axis"])
            and cache.Bounds == previous_box
            and cache.BakedMatrix == cache.MappingMatrix == IDENTITY,
            "Graphics texture cache differs from Design mapping",
        )
    origin = PointCoords(wood.Fields["origin"])
    require(
        texture.Cache.Secondary.WoodOrigin == origin
        and texture.Cache.Secondary.WoodAxis == PointCoords(wood.Fields["bordFaceAxis"]),
        "Wood cache origin or axis differs",
    )
    return origin


def compare_material(first, last):
    part1, binds1, (phys1, raw1, visual1, aspects1) = first
    part2, binds2, (phys2, raw2, visual2, aspects2) = last
    require(
        binds1 == binds2 and raw1 == raw2 and visual1 == visual2 and part1.Name != part2.Name,
        "Body material bindings or observed package identity changes differ",
    )
    physical = [
        replace(asset, Properties=tuple(p for p in asset.Properties if p.FieldName != "physmat_aspects"))
        for asset in (phys1, phys2)
    ]
    require(
        physical[0] == physical[1]
        and all(
            a.InstanceId != b.InstanceId and replace(a, InstanceId=b.InstanceId) == b
            for a, b in zip(aspects1, aspects2, strict=True)
        ),
        "Resolved physical aspect content differs",
    )
    return [
        field.name
        for field in fields(part1.Package)
        if getattr(part1.Package, field.name) != getattr(part2.Package, field.name)
    ]


def measure(directory, precursor_path):
    receipts = [(directory / f"{stage}.json").read_bytes() for stage in ("Candidate", "Reopen")]
    candidate, reopen = map(json.loads, receipts)
    require(
        candidate["stage"] == "Candidate"
        and reopen["stage"] == "Reopen"
        and candidate["status"] == reopen["status"] == "passed"
        and candidate["case"] == reopen["case"]
        and candidate["source_sha256"] == reopen["source_sha256"]
        and candidate["pid"] != reopen["pid"]
        and candidate["fusion_version"] == reopen["fusion_version"],
        "Candidate and reopen custody disagree",
    )
    precursor = load(
        precursor_path,
        candidate["candidate_sha256"],
        reopen["candidate_sha256"],
        candidate["archives"][precursor_path.name],
    )
    precursor_box = frame_bounds(precursor)
    graph = BuildGraph(precursor)
    require(
        SelectExtrusion(graph).BodyNode.Fields.get("textureMapping") is None,
        "Precursor has a body texture mapping",
    )
    states, materials, identities = [], [], []
    previous_box = precursor_box
    for name in ("VendorEdited.f3d", "VendorRestored.f3d"):
        measured_sha = reopen["archives"][name]
        model = load(directory / name, measured_sha, candidate["archives"].get(name, measured_sha))
        graph = BuildGraph(model)
        context = SelectExtrusion(graph)
        solved = frame_bounds(model)
        require(
            solved[:5] == previous_box[:5] and solved[5] != previous_box[5],
            "Expected a positive height-only frame change",
        )
        origin = mapping(model, graph, context.BodyNode, previous_box)
        identities.append((model.Asset.AssetId, model.Document.DocumentId))
        materials.append(material(model, graph, context.BodyNode))
        states.append(
            {
                "sha256": measured_sha,
                "height_parameter_cm": height_parameters(graph, context)["native_cm"],
                "solved_box_cm": solved,
                "mapping_box_cm": previous_box,
                "initialized_origin_cm": origin,
            }
        )
        previous_box = solved
    first, last = states
    require(
        identities[0][0] == identities[1][0] and identities[0][1] != identities[1][1],
        "Expected two distinct exports of one native asset",
    )
    center = tuple(
        (min_value + max_value) / 2
        for min_value, max_value in zip(precursor_box[:3], precursor_box[3:], strict=True)
    )
    origin = first["initialized_origin_cm"]
    require(
        origin == last["initialized_origin_cm"] and origin in (ZERO, center),
        "Unsupported initialized origin observation",
    )
    return {
        "group": directory.name,
        "candidate_sha256": candidate["candidate_sha256"],
        "fusion_build": candidate["fusion_version"],
        "receipt_sha256": dict(zip(("Candidate", "Reopen"), map(digest, receipts), strict=True)),
        "preceding_centroid_origin": origin == center,
        "edited": first,
        "restored": last,
        "changed_package_fields": compare_material(*materials),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read-only saved cuboid material and texture mapping evidence"
    )
    parser.add_argument(
        "--group",
        nargs=2,
        metavar=("RECEIPT_DIRECTORY", "PRE_EDIT_CANDIDATE"),
        action="append",
        type=Path,
        required=True,
    )
    args = parser.parse_args()
    report = [measure(*group) for group in args.group]
    output = json.dumps(
        {"groups": report, "new_native_run": False}, sort_keys=True, indent=2, allow_nan=False
    )
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"Material height evidence refused: {error}") from None
