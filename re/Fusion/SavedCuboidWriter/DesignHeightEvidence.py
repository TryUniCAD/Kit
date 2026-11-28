# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import re
import sys
from collections import Counter
from dataclasses import fields, is_dataclass
from hashlib import sha256
from math import isclose
from pathlib import Path
from uuid import UUID

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    MappingItems,
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Projection.ProjectNative import ProjectNative
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import CheckPrismFrame
from convert.Formats.Fusion.ContainerCodec.Assembly.RevisionMap import KChangeTypes
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import PrismSnapshot
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Records.RecordSource import CadSource

MANIFEST = Path(__file__).resolve().parents[1] / "SavedCuboidRoundTrip/Corpus/Manifest.json"
FIXTURES = {"BaselineControl", "BaselineEdited", "BaselineRestored", "HoldoutControl"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(payload):
    return sha256(payload).hexdigest()


def corpus_member(directory, name):
    path = (directory / name).resolve()
    require(path.is_relative_to(directory), "Corpus member escapes its manifest directory")
    return path.read_bytes()


def read_fixture(directory, row):
    require(row["stage_status"] == "passed", "Pinned fixture lacks a passed source observation")
    receipt_raw = corpus_member(directory, row["custody_record"])
    require(digest(receipt_raw) == row["custody_record_sha256"], "Fixture custody digest differs")
    receipt = json.loads(receipt_raw)
    raw = corpus_member(directory, row["file"])
    measured = receipt["archives"][row["custody_archive_key"]]
    require(digest(raw) == row["sha256"] == measured, "Fixture archive digest differs")
    require(
        (receipt["status"], receipt["stage"], receipt["case"], receipt["fusion_version"], receipt["pid"])
        == (
            row["stage_status"],
            row["prior_capture_stage"],
            row["prior_case"],
            row["fusion_build"],
            row["prior_pid"],
        ),
        "Fixture custody does not describe the pinned native observation",
    )
    return ReadDocument(raw)


def mapped(value):
    rows = MappingItems(value)
    result = {entry.First: entry.Second for entry in rows}
    require(len(result) == len(rows), "Ambiguous native map contains a duplicate key")
    return result


def one(values, role):
    require(len(values) == 1, f"Expected one unambiguous {role}")
    return values[0]


def guid(text, *, allow_zero=False):
    require(isinstance(text, str), "Expected a typed revision GUID")
    value = UUID(text)
    require(str(value) == text and (allow_zero or value.int != 0), "Expected a canonical revision GUID")
    return text


def height_parameters(graph, context):
    binding = context.Along
    dependent = ResolveField(graph, binding, "parameter", "Parameter")
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    rows = LinkedNodes(graph, table, "children")
    expression = TextValue(dependent.Fields["expression"])
    driver = one(tuple(row for row in rows if row.Fields["userName"] == expression), "height user parameter")
    require(dependent in rows and dependent != driver, "Model distance is not owned by its parameter table")
    require(
        dependent.Fields["isUserDefined"] is False
        and driver.Fields["isUserDefined"] is True
        and driver.Fields["dcParameter"] is None
        and dependent.Fields["unit"] == driver.Fields["unit"] == "mm"
        and graph.Resolve(dependent.Fields["dcParameter"]) == binding
        and graph.Resolve(binding.Fields["rrOwnerFeature"]) == context.Extrude
        and graph.Resolve(binding.Fields["rParentFeature"]) == context.Extrude,
        "Height must have one reciprocal owned distance and one independent user driver",
    )
    require(
        binding.Fields["isActive"] is True
        and binding.Fields["isEdited"] is False
        and binding.Fields["isEliminated"] is False
        and all(
            row.Fields["isDirty"] is False and row.Fields["isDriven"] is False for row in (driver, dependent)
        ),
        "Height driver and model slot must be in the measured solved state",
    )
    literal = TextValue(driver.Fields["expression"])
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?) mm", literal)
    require(match is not None, "Height driver requires a positive millimetre literal")
    mm = float(match[1])
    value = NumberValue(binding.Fields["value"])
    require(
        value > 0
        and value
        == NumberValue(driver.Fields["value"])
        == NumberValue(dependent.Fields["value"])
        == mm * 0.1,
        "The user literal, model parameter and extent disagree in native centimetres",
    )
    return {
        "driver": driver.Identity,
        "dependent": dependent.Identity,
        "extent": binding.Identity,
        "literal": literal,
        "native_cm": value,
        "division_by_ten_exact": mm / 10 == value,
    }


def check_geometry(model, context, height):
    history = model.Bodies[0].History
    snapshot = model.Snapshots[0].Snapshot
    require(
        isinstance(history, PrismHistory)
        and isinstance(snapshot, PrismSnapshot)
        and history.Model == snapshot.Model
        and history.TagSet == snapshot.TagSet
        and history.Model.BasePoint == (0.0, 0.0, 0.0)
        and history.History.InitialId == context.Extrude.Fields["startModelHS"]
        and history.History.CurrentId == context.Extrude.Fields["endModelHS"],
        "Expected a positive XY prism history and independently typed matching snapshot",
    )
    box = history.Model
    width, depth = box.Width / 10, box.Depth / 10
    require(
        isclose(box.Height / 10, height, rel_tol=1e-12), "Solved geometry height differs from Design extent"
    )
    for frame in (history.Frame, snapshot.Frame):
        CheckPrismFrame(box, frame)
    spans = (width, depth, height)
    center = tuple(span / 2 for span in spans)
    volume = width * depth * height
    area = 2 * (width * depth + width * height + depth * height)
    inertia = tuple(volume * sum(spans[j] ** 2 / 3 for j in range(3) if j != i) for i in range(3))
    cross = tuple(-volume * center[i] * center[j] for i, j in ((0, 1), (0, 2), (1, 2)))
    cache = ObjectFields(context.BodyNode.Fields["cache"])
    values = (
        NumberValue(cache["volume"]),
        NumberValue(cache["area"]),
        *PointCoords(cache["cog"]),
        *PointCoords(cache["moi"]),
        *PointCoords(cache["moiOffDiag"]),
    )
    expected = (volume, area, *center, *inertia, *cross)
    require(
        all(
            isclose(actual, target, rel_tol=1e-12, abs_tol=1e-12)
            for actual, target in zip(values, expected, strict=True)
        ),
        "Native physical cache differs from independent analytic cuboid properties",
    )
    return {
        "solved_width_depth_height_cm": spans,
        "volume_cm3": volume,
        "area_cm2": area,
        "centroid_cm": center,
        "hist_start": history.History.InitialId,
        "hist_end": history.History.CurrentId,
        "body_key": history.Identity.BodyKey,
    }


def check_act(model, graph, context, fixture):
    table = graph.OneClass("ACTTable", 1)
    component = graph.OneClass("ACTComponent", 1)
    occurrence = graph.OneClass("ACTInstance", 1)
    require(
        graph.Resolve(component.Fields["designComponent"], 1) == context.Component
        and graph.Resolve(occurrence.Fields["designInstance"], 1) == graph.OneClass("ComponentInstance")
        and graph.Resolve(occurrence.Fields["targetComponent"], 1) == component,
        "ACT component or occurrence does not resolve to the root Design graph",
    )
    entries = [ObjectFields(item) for item in SeriesItems(table.Fields["ACTTableEntries"])]
    owners = {
        f"{node.SegmentId}_{node.ObjectId}": node
        for node in (component, occurrence, context.Sketch, context.BodyNode)
    }
    by_owner = {}
    for entry in entries:
        target = TextValue(entry["tgtIdentifier"])
        revision = graph.Resolve(entry["rActData"], 1)
        require(
            target in owners
            and target not in by_owner
            and revision.ClassName == "RevGUIDACTDataMany"
            and revision.Fields["actIdentifier"] == target,
            "ACT revision entry is orphaned, mistyped or ambiguous",
        )
        by_owner[target] = revision
    require(
        by_owner.keys() == owners.keys()
        and set(node.Identity for node in by_owner.values())
        == {node.Identity for node in graph.ByClass("RevGUIDACTDataMany", 1)},
        "Unexpected ACT revision owners",
    )
    roles = tuple(
        (name, node)
        for name, node in zip(("component", "occurrence", "sketch", "body"), owners.values(), strict=True)
    )
    revisions = {
        name: mapped(by_owner[f"{node.SegmentId}_{node.ObjectId}"].Fields["revGuidMap"])
        for name, node in roles
    }
    table_domains = mapped(table.Fields["revisionGuidForChangeType"])
    body_domains = {"Appearance", "Geometry"}
    if fixture in {"BaselineControl", "HoldoutControl"}:
        body_domains |= {"PhysicalMaterial", "Properties"}
    require(
        set(table_domains) == set(revisions["component"]) == set(revisions["occurrence"]) == set(KChangeTypes)
        and set(revisions["sketch"]) == {"Appearance", "Geometry", "Properties"}
        and set(revisions["body"]) == body_domains,
        "Unexpected saved ACT change domains",
    )
    cache = ObjectFields(context.BodyNode.Fields["cache"])
    snapshot = guid(table.Fields["AssetRevGuid"])
    table_geometry = guid(table.Fields["RevisionGuid"])
    body_geometry = guid(cache["revisionGuid"])
    require(
        model.Document.AssetId == model.Asset.AssetId
        and snapshot == model.Asset.SnapshotId
        and table_geometry == table_domains["Geometry"]
        and body_geometry == revisions["body"]["Geometry"],
        "Asset, table or physical cache revision join disagrees",
    )
    physical = guid(
        one(
            tuple(value for key, value in model.Asset.Properties if key == "physicalChangeGuid"),
            "physical change GUID",
        )
    )
    design_revision = guid(context.Component.Fields["revisionGuid"])
    require(
        len({snapshot, table_geometry, body_geometry, physical, design_revision}) == 5,
        "Distinct native revision roles unexpectedly alias",
    )
    return {
        role: {domain: guid(value, allow_zero=True) for domain, value in domains.items()}
        for role, domains in {"table": table_domains, **revisions}.items()
    }


def check_clocks(graph, context, history):
    updates = graph.ByClass("DynamicUpdateData")
    by_owner = {}
    for row in updates:
        owner = graph.Resolve(row.Fields["rOwnerNode"])
        require(
            owner.Identity not in by_owner and graph.Resolve(owner.Fields["rDynamicUpdateData"]) == row,
            "Dynamic update data must be reciprocal and unique per owner",
        )
        stamp = row.Fields["timeStamp"]
        require(type(stamp) is int and stamp > 0, "Unexpected dynamic update timestamp")
        by_owner[owner.Identity] = stamp
    checked = 0
    for row in updates:
        for ref, stamp in mapped(row.Fields["predecessors"]).items():
            target = graph.Resolve(ref).Identity
            require(
                target in by_owner and by_owner[target] == stamp,
                "Predecessor timestamp differs from its referenced owner",
            )
            checked += 1
    require(
        history.Identity.AuthoredMicros == by_owner[context.Extrude.Identity],
        "Body history authoring time does not join its extrusion update",
    )
    return checked


def check_caches(model, graph, context):
    datum = graph.OneClass("EntityDataRef")
    cached_plane = one(LinkedNodes(graph, datum, "caches"), "cached datum plane")
    require(cached_plane.ClassName == "ETCachedPlane", "Unexpected datum cache kind")
    progenitor = ResolveField(graph, cached_plane, "progenitor", "EntityProgenitor")
    recipe = ResolveField(graph, progenitor, "m_entityRecipe", "EntityRecipe")
    original = ResolveField(graph, datum, "rRecipe", "EntityRecipe")
    require(
        graph.ResolveId(recipe.Fields["m_entityId"]) == graph.ResolveId(original.Fields["m_entityId"]),
        "Cached datum provenance does not identify the original support",
    )
    cache_nodes = [cached_plane, progenitor, recipe]
    for kind in ("DRMatrix", "ModelDataRef"):
        cache = one(LinkedNodes(graph, graph.OneClass(kind), "caches"), f"{kind} matrix cache")
        require(cache.ClassName == "ETCachedMatrix3d", "Unexpected matrix cache kind")
        CheckIdentity(cache.Fields["rCachedGeometry"])
        cache_nodes.append(cache)
    for kind, field in (("SketchRegionRef", "caches"), ("DcExtrudeToolBody", "toolbodyCaches")):
        cache = one(LinkedNodes(graph, graph.OneClass(kind), field), f"{kind} topology cache")
        require(cache.ClassName == "ETCachedTopology", "Unexpected topology cache kind")
        scope = ObjectFields(cache.Fields["scope"])
        require(
            scope
            == {
                "assetId": model.Asset.AssetId,
                "segmentId": 0,
                "scopeIdType": 2,
                "scopeEntityIdentifier": context.Component.Fields["persistentId"],
            },
            "Cached topology is outside the active component scope",
        )
        cache_nodes.append(cache)
    require(
        len({node.Identity for node in cache_nodes}) == len(cache_nodes),
        "Cached design records unexpectedly alias",
    )
    return tuple(node.Identity for node in cache_nodes)


def references(value):
    if isinstance(value, (LocalRef, SegmentRef)):
        yield value
    elif isinstance(value, tuple):
        for item in value:
            yield from references(item)
    elif is_dataclass(value):
        for field in fields(value):
            yield from references(getattr(value, field.name))


def inspect(model, archive_digest, fixture):
    require(
        tuple(
            (segment.Metadata.Header.SegmentId, segment.Metadata.Header.Segment) for segment in model.Segments
        )
        == ((0, SegmentKind.KDesign), (1, SegmentKind.KAct), (2, SegmentKind.KBrowser))
        and not any(segment.BulkSlack for segment in model.Segments)
        and (len(model.Bodies), len(model.Snapshots), len(model.Configurations), len(model.Materials))
        == (1, 1, 2, 1)
        and not model.Asset.Links
        and model.Graphics is not None,
        "Unsupported saved cuboid segment or auxiliary inventory",
    )
    document = ProjectNative(model, CadSource("fusion.f3d", "", archive_digest))
    require(
        set(document.metadata) == {"fusion.native_state", "fusion.read_only"}
        and document.metadata["fusion.read_only"] is True,
        "Expected the strict read-only saved cuboid profile",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    require(
        len(graph.ByClass("SketchGeomConstraint")) == 4 and len(graph.ByClass("FusionSketchLinearDim")) == 2,
        "Expected the fixed-corner constrained rectangle profile",
    )
    height = height_parameters(graph, context)
    history = model.Bodies[0].History
    browser_targets = Counter(
        graph.Resolve(ref, 2).SegmentId for ref in references(model.Segments[2].Records)
    )
    revisions = check_act(model, graph, context, fixture)
    return (
        graph,
        revisions,
        {
            "height": height,
            "geometry": check_geometry(model, context, height["native_cm"]),
            "revision_domains": {role: sorted(domains) for role, domains in revisions.items()},
            "distinct_revision_roles": 5,
            "timestamp_joins": check_clocks(graph, context, history),
            "cache_records": check_caches(model, graph, context),
            "browser_reference_counts": dict(browser_targets),
        },
    )


def compare_pair(before, after):
    first, first_graph, first_revisions, first_report = before
    last, last_graph, last_revisions, last_report = after
    require(
        first.Asset.AssetId == last.Asset.AssetId and first.Document.DocumentId != last.Document.DocumentId,
        "Edited and restored exports must identify one asset and distinct documents",
    )
    require(
        first.Segments[2].Records == last.Segments[2].Records
        and first.Segments[2].Metadata == last.Segments[2].Metadata,
        "Saved height pair changes Browser records or their metadata",
    )
    require(
        first_report["height"]["native_cm"] != last_report["height"]["native_cm"]
        and first_report["geometry"]["solved_width_depth_height_cm"][:2]
        == last_report["geometry"]["solved_width_depth_height_cm"][:2]
        and all(
            first_report["height"][role] == last_report["height"][role]
            for role in ("driver", "dependent", "extent")
        ),
        "Saved pair does not isolate a height change on the same Design entities",
    )
    old, new = first_graph.Nodes, last_graph.Nodes
    changed = Counter(
        key[0]
        for key in old.keys() & new.keys()
        if old[key].Fields != new[key].Fields or old[key].Frame != new[key].Frame
    )
    require(changed == {0: 35, 1: 4}, "Saved pair has an unmeasured matched-record change footprint")
    require(
        {old[key].Identity for key in old.keys() - new.keys()} == set(first_report["cache_records"])
        and {new[key].Identity for key in new.keys() - old.keys()} == set(last_report["cache_records"]),
        "Unexplained Design or auxiliary entity allocation changes in the height pair",
    )
    prediction = {
        "table": ["Appearance", "Geometry", "Properties", "StructureChange"],
        "component": ["Appearance", "Geometry", "Properties", "StructureChange"],
        "occurrence": [],
        "sketch": ["Geometry"],
        "body": ["Appearance", "Geometry"],
    }
    domains = {}
    for owner, values in first_revisions.items():
        candidate = last_revisions[owner]
        require(values.keys() == candidate.keys(), "ACT revision-domain inventory changed")
        domains[owner] = sorted(key for key in values if values[key] != candidate[key])
    require(domains == prediction, "Saved pair has unmeasured ACT domain changes")
    return {
        "changed_matched_records_by_segment": dict(changed),
        "replaced_cache_records": len(old.keys() - new.keys()),
        "changed_revision_domains": domains,
        "browser_records_equal": True,
    }


def main():
    raw = MANIFEST.read_bytes()
    manifest = json.loads(raw)
    rows = manifest["fixtures"]
    require(
        type(manifest["schema"]) is int
        and manifest["schema"] == 1
        and len(rows) == len(FIXTURES)
        and {row["id"] for row in rows} == FIXTURES,
        "Unexpected saved cuboid evidence manifest",
    )
    artifacts = {}
    for row in rows:
        model = read_fixture(MANIFEST.parent, row)
        graph, revisions, report = inspect(model, row["sha256"], row["id"])
        artifacts[row["id"]] = (model, graph, revisions, {"sha256": row["sha256"], **report})
    reports = {key: value[3] for key, value in artifacts.items()}
    require(
        reports["HoldoutControl"]["height"]["literal"] == "31.4 mm"
        and not reports["HoldoutControl"]["height"]["division_by_ten_exact"],
        "Missing the independent 31.4 mm precision witness",
    )
    pair = compare_pair(artifacts["BaselineEdited"], artifacts["BaselineRestored"])
    output = json.dumps(
        {
            "manifest_sha256": digest(raw),
            "fixtures": reports,
            "paired_edit": pair,
            "conversion_output": False,
            "native_acceptance": "unmeasured",
        },
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"Design height evidence refused: {error}") from None
