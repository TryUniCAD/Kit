# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid5

from convert.Formats.Fusion.AssetCodec.ConfigLayout import KConfigClasses
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import CheckDocConfig
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.ConfigName import ConfigName
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import GroupFields

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH / "SavedCameras"))
import CameraRequest as Cameras

SCHEMA = 1
SCOPE = "fixed_cuboid_empty_configuration_envelope"
OPEN_SCOPE = [item for item in Cameras.OPEN_SCOPE if item != "saved_configuration_parts"] + [
    "nonempty_configured_designs"
]
PART_PREFIX = "DesignConfigurationTable.BlobParts/"
BLOB_SERIALIZER = "130A0711-4E92-4FCD-AADE-B9C82238BB27"
ROLES = ("table", "rule")
VOCABULARY = {
    "table" if label == "DesignConfigurationTable" else "rule": (guid, label, extension)
    for guid, (label, extension) in KConfigClasses.items()
}
ROOTS = {label + "SerializerTrigger": role for role, (_, label, _) in VOCABULARY.items()}
require = Cameras.require


def configured_order(value):
    require(
        type(value) is list and value in ([], ["table", "rule"], ["rule", "table"]),
        "Configuration parts must explicitly list neither member or one table and one rule",
    )
    return value


def validate(request):
    Cameras.exact_fields(request, ("schema", "scope", "camera_request", "configuration_parts"), "request")
    require(
        type(request["schema"]) is int and request["schema"] == SCHEMA and request["scope"] == SCOPE,
        "Unsupported empty configuration envelope request schema",
    )
    return {
        **request,
        "camera_request": Cameras.validate(request["camera_request"]),
        "configuration_parts": configured_order(request["configuration_parts"]),
    }


def configuration_order(model):
    CheckDocConfig(model)
    triggers = {}
    for segment in model.Segments:
        object_counts = {}
        for record in segment.Records:
            object_counts[record.ObjectId] = object_counts.get(record.ObjectId, 0) + 1
        for record in segment.Records:
            groups = tuple(group.ClassGuid.upper() for group in record.Groups)
            root = record.Frame.RootId
            if root not in ROOTS and not any(guid in KConfigClasses for guid in groups):
                continue
            require(
                segment.Metadata.Header.SegmentId == 0
                and record.IsPrimary
                and root in ROOTS
                and object_counts[record.ObjectId] == 1
                and segment.Metadata.StoredIds.count(record.ObjectId) == 1
                and record.Frame.Subjects is None
                and record.Frame.Metadata is None,
                "Configuration trigger is not an unadorned primary Design root",
            )
            role = ROOTS[root]
            guid, _, _ = VOCABULARY[role]
            fields = GroupFields(record.Groups)
            require(
                groups == (guid, BLOB_SERIALIZER)
                and not record.Groups[0].Fields
                and len(record.Groups[1].Fields) == 1
                and set(fields) == {"partName"}
                and type(fields["partName"]) is str
                and role not in triggers,
                "Configuration trigger schema, fields or ownership are unsupported",
            )
            triggers[role] = PART_PREFIX + fields["partName"]
    require(tuple(triggers) in ((), ROLES), "Configuration triggers require the ordered Design root pair")
    order = configured_order([part.KindValue for part in model.Configurations])
    identities = set()
    for part in model.Configurations:
        role = ConfigName(part.Name)
        require(
            role == part.KindValue and triggers.get(role) == part.Name,
            "Configuration sidecar is alien to its Design trigger",
        )
        _, label, suffix = VOCABULARY[role]
        identity = part.Name.removeprefix(PART_PREFIX + label + ".").removesuffix(suffix)
        require(identity not in identities, "Configuration table and rule share an identity")
        identities.add(identity)
    require(set(order) == set(triggers), "Configuration trigger is missing its sidecar")
    return order


def projection(model, public):
    return validate(
        {
            "schema": SCHEMA,
            "scope": SCOPE,
            "camera_request": Cameras.projection(model, public),
            "configuration_parts": configuration_order(model),
        }
    )


def prepare(source):
    return projection(*Cameras.open_saved(source))


def stage_configurations(author, order):
    require(
        not any(entity.ClassName in ROOTS or entity.RootName in ROOTS for entity in author.Entities),
        "Fresh author already has configuration triggers",
    )
    parts = {}
    for role in ROLES:
        _, label, suffix = VOCABULARY[role]
        identity = uuid5(UUID(author.AssetId), f"kit:fusion:empty-configuration:{role}")
        name = f"{label}.{identity}{suffix}"
        root = label + "SerializerTrigger"
        author.Allocate(f"configuration_{role}", root, RootName=root, Fields={"partName": name})
        parts[role] = ConfigPart(PART_PREFIX + name, role)
    return tuple(parts[role] for role in order)


def unify_trigger_records(records):
    combined = []
    source = iter(records)
    for primary in source:
        root = primary.Frame.RootId
        if root in ROOTS:
            continuation = next(source, None)
            guid, _, _ = VOCABULARY[ROOTS[root]]
            require(
                continuation is not None
                and primary.IsPrimary
                and not continuation.IsPrimary
                and primary.ObjectId == continuation.ObjectId
                and primary.Frame == continuation.Frame
                and tuple(group.ClassGuid.upper() for group in primary.Groups) == (guid,)
                and tuple(group.ClassGuid.upper() for group in continuation.Groups) == (BLOB_SERIALIZER,),
                "Fresh configuration trigger record structure changed",
            )
            primary = replace(primary, Groups=primary.Groups + continuation.Groups)
        combined.append(primary)
    return tuple(combined)


def part_receipts(model, archive):
    names = [KAssetPrefix + part.Name for part in model.Configurations]
    require(
        [
            name
            for name in archive.namelist()
            if name.startswith(KAssetPrefix + PART_PREFIX) and not name.endswith("/")
        ]
        == names,
        "Configuration archive members disagree with the typed part order",
    )
    require(
        all(archive.read(name) == b"{}" for name in names),
        "Generated configuration payload is not canonical empty JSON",
    )
    return [
        dict(kind=part.KindValue, archive_member=name)
        for part, name in zip(model.Configurations, names, strict=True)
    ]
