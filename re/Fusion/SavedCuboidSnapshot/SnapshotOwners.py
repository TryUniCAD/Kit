# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass
from uuid import UUID, uuid5

from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import PartScope
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole


UINT64_MAX = (1 << 64) - 1
TOOL_CACHE = "snapshot_tool_cache"
REGION_CACHE = "snapshot_region_cache"


@dataclass(frozen=True, slots=True)
class SnapshotRootPlan:
    tool_solid: int
    profile_region: int
    sketch_sheet: int

    def scan_order(self):
        order = (self.tool_solid, self.profile_region, self.sketch_sheet)
        if any(type(root) is not int or not 0 < root < UINT64_MAX for root in order) or len(set(order)) != len(order):
            raise ValueError("Snapshot roots require three distinct positive IDs and room for nextId")
        return order


def stage_snapshot_owners(
    author: AuthorState,
    plan: SnapshotRootPlan,
    *,
    addresses: tuple[int, int, int],
) -> str:
    """Set snapshot ownership on a fresh research author graph. Return the matching archive member name."""
    if not isinstance(plan, SnapshotRootPlan):
        raise ValueError("Explicit snapshot root plan required")
    order = plan.scan_order()
    if type(addresses) is not tuple or len(addresses) != len(order) or any(
        type(address) is not int or not 0 <= address <= UINT64_MAX for address in addresses
    ):
        raise ValueError("Supply one experimental unsigned 64-bit address per snapshot root")

    spec = author.SpecValue
    if spec.ProfileKind != "cuboid" or spec.ConstrainRectangle is not True or spec.Features or spec.TaperDegrees != 0:
        raise ValueError("Snapshot seam requires a fresh fixed-corner cuboid")
    sketch = SketchRole(author)
    classes = {
        "component": "FusionComponent",
        "cache_bodies": "Bodies",
        "cache_serializer": "BRepSerializer",
        "passive_ids": "PassiveIdGenerator",
        "dc_extrude": "DcExtrudeFeature",
        "profile_model": "ModelDataRef",
        "profile_region": "SketchRegionRef",
        "extrude_tool": "DcExtrudeToolBody",
        sketch: "MSketch",
    }
    if not classes.keys() <= author.Roles.keys() or {TOOL_CACHE, REGION_CACHE} & author.Roles.keys():
        raise ValueError("Snapshot owner roles are absent or already allocated")
    entities = {role: author.FindEntity(role) for role in classes}
    if any(entities[role].ClassName != expected for role, expected in classes.items()):
        raise ValueError("Snapshot owner role has an unexpected class")

    ref = author.Reference
    bindings = {
        "component": {"rCacheBodies": ref("cache_bodies")},
        "cache_bodies": {"rBRepSerializer": ref("cache_serializer")},
        "cache_serializer": {"rBodies": ref("cache_bodies"), "topEntityPIDGenerator": ref("passive_ids")},
        "dc_extrude": {"rExtrudeToolBody": ref("extrude_tool"), "profileDataRefs": [ref("profile_model")]},
        "profile_model": {"dataRefs": [ref("profile_region")]},
    }
    if any(entities[role].FieldValues.get(field) != target
           for role, fields in bindings.items() for field, target in fields.items()):
        raise ValueError("Snapshot owner references do not match the constructor graph")

    pristine = {
        "cache_bodies": {"groupChildren": [], "passiveIdGenerator": None},
        "cache_serializer": {"partName": "", "mapBodyId": []},
        "passive_ids": {"nextId": 0, "scanOrderIndex": [], "addressOfTopEntities": []},
        "profile_region": {"caches": []},
        "extrude_tool": {"toolbodyCaches": []},
        sketch: {"bodyId": 0},
    }
    for role, fields in pristine.items():
        entity = entities[role]
        lineage = author.Lineage(author.ByName[entity.ClassName].Value.ClassGuid)
        defaults = {field: value for schema in reversed(lineage) for field, value in author.Defaults.get(schema.NameValue, {}).items()}
        if any(entity.FieldValues.get(field, defaults.get(field)) != expected for field, expected in fields.items()):
            raise ValueError(f"Snapshot owner {role} is already populated")
    if "ETCachedTopology" not in author.ByName:
        raise ValueError("Constructor lacks the snapshot topology cache schema")

    # The UUID namespace separates the snapshot member from history, document and asset revision UUIDs.
    part_id = uuid5(UUID(author.AssetId), f"kit:fusion:cuboid-snapshot:{UUID(author.ComponentId)}")
    part_name = f"BREP.{part_id}.smb"
    for role, root in ((TOOL_CACHE, plan.tool_solid), (REGION_CACHE, plan.profile_region)):
        author.Allocate(role, "ETCachedTopology", Fields={"cachedEntityId": root, "scope": PartScope(author), "progenitor": None})
    author.Change("cache_serializer", partName=part_name)
    author.Change("passive_ids", nextId=max(order) + 1, scanOrderIndex=list(order), addressOfTopEntities=list(addresses))
    author.Change("extrude_tool", toolbodyCaches=[ref(TOOL_CACHE)])
    author.Change("profile_region", caches=[ref(REGION_CACHE)])
    author.Change(sketch, bodyId=plan.sketch_sheet)
    return f"Breps.BlobParts/{part_name}"
