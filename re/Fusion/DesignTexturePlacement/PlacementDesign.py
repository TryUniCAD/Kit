# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from dataclasses import fields, is_dataclass, replace
from sys import float_info

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

from PlacementRequest import Appearance, SCHEMA, SCOPE, origin_bits, origin_point, require, validate
from AppearanceGraph import projection as appearance_projection
from MaterialGraph import TEXTURE_MAPPING_GUID

AXES = ("x", "y", "z")
ZERO_AXIS = (0.0, 0.0, 0.0)
BOX_LIMIT = float_info.max
LAYERED, ASM, WOOD = "LayeredTextureMapping", "ASMTextureMapping", "ProceduralWoodTextureMapping"
MAPPING_TYPES = {LAYERED, ASM, WOOD}
PLAIN_FRAME = EntityFrame("", None, None)
EXCLUSIVE = "Design texture placement requires one exclusive body mapping graph"
LAYOUTS = {
    LAYERED: ((LAYERED, ("activeLayer", "layers")),),
    ASM: ((ASM, ()), ("AutoTextureMapping", ()), ("TextureMapping2D", ())),
    WOOD: (
        (WOOD, ("bordFaceAxis", "origin", "originInitilized")),
        ("ProceduralTextureMapping3D", ()),
        ("TextureMapping3D", ()),
    ),
}
BASE_FIELDS = ("axis", "bakedTransformInGeometry", "textureMappingBoundingBox", "textureMappingTransform")


def vector(value):
    return dict(zip(AXES, value, strict=True))


def stage_placement(author, origin):
    require(author.FindEntity("body").FieldValues.get("textureMapping") is None, EXCLUSIVE)
    require(not any(entity.ClassName in MAPPING_TYPES for entity in author.Entities), EXCLUSIVE)
    bounds = author.MakeGroup(
        "BBoxValue", {"max": vector((-BOX_LIMIT,) * 3), "min": vector((BOX_LIMIT,) * 3)}
    )
    base = {
        "axis": vector(ZERO_AXIS),
        "bakedTransformInGeometry": {"identity": True},
        "textureMappingBoundingBox": [bounds],
        "textureMappingTransform": {"identity": True},
    }
    author.Allocate("placement_asm", ASM, Fields=base)
    author.Allocate(
        "placement_wood",
        WOOD,
        Fields={
            **base,
            "bordFaceAxis": vector(ZERO_AXIS),
            "origin": vector(origin),
            "originInitilized": True,
        },
    )
    author.Allocate(
        "placement_layers",
        LAYERED,
        Fields={
            **base,
            "activeLayer": 0,
            "layers": [
                {"key": 2, "value": author.Reference("placement_asm")},
                {"key": 3, "value": author.Reference("placement_wood")},
            ],
        },
    )
    author.Change("body", textureMapping=author.Reference("placement_layers"))
    return author


def point(value):
    require(
        isinstance(value, ValueStruct)
        and tuple(field.FieldName for field in value.Fields) == AXES
        and all(type(field.Value) is float for field in value.Fields),
        "Unsupported Design texture placement vector fields",
    )
    return origin_point([field.Value for field in value.Fields])


def check_empty_bounds(value, codes):
    require(
        isinstance(value, ValueObject) and len(value.Groups) == 1,
        "Unsupported Design texture placement bounds object",
    )
    (box,) = value.Groups
    require(
        box.ClassGuid.upper() == codes["BBoxValue"]
        and box.Opaque is None
        and tuple(field.FieldName for field in box.Fields) == ("max", "min"),
        "Unsupported Design texture placement bounds fields",
    )
    upper, lower = (point(field.Value) for field in box.Fields)
    require(
        upper == (-BOX_LIMIT,) * 3 and lower == (BOX_LIMIT,) * 3,
        "Unsupported Design texture placement bounds; expected the inverted finite empty box",
    )


def check_row(node, codes):
    expected = (*LAYOUTS[node.ClassName], ("TextureMapping", BASE_FIELDS))
    observed = tuple(
        (group.ClassGuid.upper(), tuple(field.FieldName for field in group.Fields)) for group in node.Groups
    )
    require(
        observed == tuple((codes[name], names) for name, names in expected)
        and node.Frame == PLAIN_FRAME
        and all(group.Opaque is None for group in node.Groups),
        "Unsupported Design texture placement stored fields or frame",
    )
    values = node.Fields
    require(
        origin_bits(point(values["axis"])) == origin_bits(ZERO_AXIS),
        "Unsupported Design texture placement axis",
    )
    require(
        values["bakedTransformInGeometry"] == MatrixValue(None)
        and values["textureMappingTransform"] == MatrixValue(None),
        "Unsupported Design texture placement transform; expected compact identity",
    )
    check_empty_bounds(values["textureMappingBoundingBox"], codes)


def references(value, segment, mapping_guids):
    if isinstance(value, LocalRef):
        yield segment, value.ObjectId
    elif isinstance(value, SegmentRef):
        yield value.SegmentId, value.ObjectId
    elif isinstance(value, CrossRef):
        # A foreign reference cannot be the exclusive local owner of a mapping.
        if value.TypeGuid.upper() in mapping_guids:
            raise ValueError(EXCLUSIVE)
    elif isinstance(value, tuple):
        for child in value:
            yield from references(child, segment, mapping_guids)
    elif is_dataclass(value):
        for field in fields(value):
            yield from references(getattr(value, field.name), segment, mapping_guids)


def check_ownership(model, body, layered, asm, wood):
    expected_refs = Counter(
        {
            (body.ObjectId, layered.ObjectId): 1,
            (layered.ObjectId, asm.ObjectId): 1,
            (layered.ObjectId, wood.ObjectId): 1,
        }
    )
    mapping_ids = {layered.ObjectId, asm.ObjectId, wood.ObjectId}
    mapping_guids = {group.ClassGuid.upper() for node in (layered, asm, wood) for group in node.Groups}
    observed_refs = Counter()
    records = Counter()
    owners = Counter()
    for part in model.Segments:
        segment = part.Metadata.Header.SegmentId
        if segment == body.SegmentId:
            require(
                not mapping_ids.intersection(part.Metadata.StoredIds)
                and not any(row.ObjectId in mapping_ids for row in part.Metadata.Continuations)
                and Counter(row.ObjectId for row in part.Metadata.Primary if row.ObjectId in mapping_ids)
                == Counter(mapping_ids),
                EXCLUSIVE,
            )
            for entry in part.Metadata.Classes:
                for owner in set(entry.OwnerIds) & mapping_ids:
                    owners[owner, entry.ClassGuid.upper()] += entry.OwnerIds.count(owner)
        for row in part.Records:
            local = segment == body.SegmentId
            if local and row.ObjectId in mapping_ids:
                require(row.IsPrimary and row.Frame == PLAIN_FRAME, EXCLUSIVE)
                records[row.ObjectId] += 1
            for target_segment, target in references((row.Frame, row.Groups), segment, mapping_guids):
                if target_segment == body.SegmentId and target in mapping_ids:
                    require(local, EXCLUSIVE)
                    observed_refs[row.ObjectId, target] += 1
    require(
        records == Counter(mapping_ids)
        and owners
        == Counter((node.ObjectId, node.Groups[0].ClassGuid.upper()) for node in (layered, asm, wood))
        and observed_refs == expected_refs,
        EXCLUSIVE,
    )
    return mapping_ids


def read_placement(model):
    require(model.Graphics is None, "Design texture placement requires no graphics scene")
    graph = BuildGraph(model)
    body = SelectExtrusion(graph).BodyNode
    binding = body.Fields.get("textureMapping")
    require(isinstance(binding, LocalRef), EXCLUSIVE)
    layered = graph.Resolve(binding, body.SegmentId)
    require(body.SegmentId == 0 and layered.ClassName == LAYERED, EXCLUSIVE)
    values = layered.Fields
    layers, active = values.get("layers"), values.get("activeLayer")
    require(
        type(active) is int
        and active == 0
        and isinstance(layers, ValueMap)
        and len(layers.Entries) == 2
        and tuple(entry.First for entry in layers.Entries) == (2, 3)
        and all(type(entry.First) is int and isinstance(entry.Second, LocalRef) for entry in layers.Entries),
        "Unsupported Design texture placement selector or layer roles",
    )
    asm, wood = (graph.Resolve(entry.Second, body.SegmentId) for entry in layers.Entries)
    inventory = {
        key
        for key, node in graph.Nodes.items()
        if graph.HasBase(node, "TextureMapping")
        or any(group.ClassGuid.upper() == TEXTURE_MAPPING_GUID for group in node.Groups)
    }
    require(
        asm.ClassName == ASM
        and wood.ClassName == WOOD
        and len(inventory) == 3
        and inventory == {(node.SegmentId, node.ObjectId) for node in (layered, asm, wood)},
        EXCLUSIVE,
    )
    codes = {schema.NameValue: schema.Value.ClassGuid.upper() for schema in ReadNames()}
    for node in (layered, asm, wood):
        check_row(node, codes)
    require(
        wood.Fields["originInitilized"] is True,
        "Unsupported Design texture placement uninitialized wood origin",
    )
    require(
        origin_bits(point(wood.Fields["bordFaceAxis"])) == origin_bits(ZERO_AXIS),
        "Unsupported Design texture placement wood board axis",
    )
    return point(wood.Fields["origin"]), body, check_ownership(model, body, layered, asm, wood)


def appearance_view(model, body, mapping_ids):
    def remove_attachment(row):
        if row.ObjectId != body.ObjectId:
            return row
        return replace(
            row,
            Groups=tuple(
                replace(
                    group,
                    Fields=tuple(
                        replace(field, Value=None) if field.FieldName == "textureMapping" else field
                        for field in group.Fields
                    ),
                )
                for group in row.Groups
            ),
        )

    segments = []
    for part in model.Segments:
        if part.Metadata.Header.SegmentId == body.SegmentId:
            metadata = replace(
                part.Metadata,
                Classes=tuple(
                    replace(row, OwnerIds=tuple(value for value in row.OwnerIds if value not in mapping_ids))
                    for row in part.Metadata.Classes
                ),
                Primary=tuple(row for row in part.Metadata.Primary if row.ObjectId not in mapping_ids),
            )
            part = replace(
                part,
                Metadata=metadata,
                Records=tuple(
                    remove_attachment(row) for row in part.Records if row.ObjectId not in mapping_ids
                ),
            )
        targets = tuple(
            target
            for target in part.Profile.ExternalTargets
            if (target.SegmentId != body.SegmentId or target.ObjectId not in mapping_ids)
        )
        segments.append(replace(part, Profile=replace(part.Profile, ExternalTargets=targets)))
    return replace(model, Segments=tuple(segments))


def projection(model, public):
    origin, body, mapping_ids = read_placement(model)
    # Validate the exclusive graph before separating it for the old material scope.
    # The complete native-state model still belongs to the original public readback.
    nested = appearance_projection(appearance_view(model, body, mapping_ids), public)
    request = {"schema": SCHEMA, "scope": SCOPE, "appearance_request": nested, "wood_origin_cm": list(origin)}
    validate(request)
    return request


def prepare(source):
    return projection(*Appearance.Material.Config.Cameras.open_saved(source))
