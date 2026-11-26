"""Author the browser-first settings schedule for the direct-owned P03 sketch."""

from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module
from unittest.mock import patch

from PairedCaptureIntake import require
from convert.Formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.Formats.Fusion.ContainerCodec.Browser.ComponentLinks import KComponentLinks
from convert.Formats.Fusion.ContainerCodec.Browser.ObserverCounts import ObserverCounts
from convert.Formats.Fusion.DocumentCodec.Records.DraftSubjects import DraftSubjects
from convert.Formats.Fusion.DocumentCodec.Rectangle.RectangleRoles import (
    KCornerRoles,
    KLineRoles,
)
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField


DIMENSION_ROLES = ("width_mm", "height_mm")
ORDER_ERROR = "P03 generated settings observers differ from the browser-first schedule"
FRAME_ERROR = "P03 authored line normals require the linked positive XY sketch frame"


def _browser_observers():
    observers = tuple(
        (entry.RoleName, entry.ClassName)
        for entry in KBrowserNodes
        for target in (*KComponentLinks.get(entry.RoleName, ()), entry.TargetRole)
        if target == "settings"
    )
    require(
        observers == (
            ("settings", "DocumentSettingsBrowserEntry"),
            ("pmi_settings", "PMISettingsBrowserEntry"),
        ),
        ORDER_ERROR,
    )
    return observers


def _design_observers(author):
    settings = author.FindEntity("settings")
    dimensions = tuple(
        entity for entity in author.Entities if "settings" in entity.Subjects
    )
    parameters = tuple(
        entity for entity in author.Entities if entity.ClassName == "Parameter"
    )
    require(
        author.SpecValue.ProfileKind == "cuboid"
        and author.SpecValue.ConstrainRectangle is True
        and not author.SpecValue.Features
        and settings.ClassName == "CommonDataAssetSettings"
        and len(parameters) == 4
        and all(row.FieldValues.get("isUserDefined") is False for row in parameters)
        and tuple(entity.RoleName for entity in dimensions)
        == ("width_dimension", "depth_dimension")
        and all(
            entity.ClassName == "FusionSketchLinearDim"
            and entity.ParentRole == SketchRole(author)
            and entity.Subjects.count("settings") == 1
            for entity in dimensions
        ),
        ORDER_ERROR,
    )
    return author.Roles[settings.RoleName], dimensions


@contextmanager
def schedule_settings():
    """Use one direct-owned author while emitting its design and browser segments."""
    frame = import_module("convert.Formats.Fusion.DocumentCodec.Records.DraftFrame")
    browser = import_module("convert.Formats.Fusion.ContainerCodec.Browser.BuildBrowser")
    require(
        frame.DraftSubjects is DraftSubjects and browser.ObserverCounts is ObserverCounts,
        ORDER_ERROR,
    )
    browser_count = len(_browser_observers())
    plan = None
    packed = False

    def draft_subjects(author, entity):
        nonlocal plan
        subjects = DraftSubjects(author, entity)
        if "settings" not in entity.Subjects:
            return subjects
        if plan is None:
            settings_id, dimensions = _design_observers(author)
            plan = author, settings_id, dimensions
        planned_author, settings_id, dimensions = plan
        (ordinal,) = tuple(i for i, row in enumerate(dimensions) if entity is row)
        target = LocalRef(settings_id)
        require(
            author is planned_author
            and subjects is not None
            and tuple(row.ObserverIndex for row in subjects if row.Target == target)
            == (ordinal,),
            ORDER_ERROR,
        )
        return tuple(
            replace(row, ObserverIndex=browser_count + row.ObserverIndex)
            if row.Target == target
            else row
            for row in subjects
        )

    def browser_counts(records):
        nonlocal packed
        counts = ObserverCounts(records)
        require(plan is not None, ORDER_ERROR)
        author, settings_id, dimensions = plan
        targets = (LocalRef(settings_id), SegmentRef(settings_id, 0))
        actual = tuple(
            (record.ObjectId, subject.ObserverIndex)
            for record in records
            for subject in record.Frame.Subjects or ()
            if subject.Target in targets
        )
        expected = tuple(
            (author.Roles[entity.RoleName], rank)
            for rank, entity in enumerate(dimensions, start=browser_count)
        )
        require(
            actual == expected and counts.get(settings_id) == browser_count + len(expected),
            ORDER_ERROR,
        )
        # These two Browser records consume the reserved initial slots in KBrowserNodes order.
        del counts[settings_id]
        packed = True
        return counts

    with (
        patch.object(frame, "DraftSubjects", draft_subjects),
        patch.object(browser, "ObserverCounts", browser_counts),
    ):
        yield
        require(packed, ORDER_ERROR)


def check_settings_order(graph):
    settings = graph.OneClass("CommonDataAssetSettings")
    sketch = graph.OneClass("MSketch")
    owner = ResolveField(graph, sketch, "rDcNode", "DcSketch")
    dimensions = LinkedNodes(graph, sketch, "dimensions")
    bindings = LinkedNodes(graph, owner, "dcParameters")
    require(
        len(dimensions) == len(bindings) == 2
        and len({node.Identity for node in dimensions}) == 2
        and len({node.Identity for node in bindings}) == 2,
        ORDER_ERROR,
    )
    browser = tuple(
        (role, graph.OneClass(class_name, SegmentId=2))
        for role, class_name in _browser_observers()
    )
    for dimension, binding, role, code in zip(
        dimensions, bindings, DIMENSION_ROLES, (1 << 22, 1 << 23), strict=True
    ):
        parameter = ResolveField(graph, binding, "parameter", "Parameter")
        require(
            dimension.ClassName == "FusionSketchLinearDim"
            and dimension.Fields["constraintType"] == code
            and ResolveField(graph, dimension, "ParentNode", "MSketch") == sketch
            and ResolveField(graph, dimension, "rParent", "MSketch") == sketch
            and ResolveField(graph, dimension, "dcParameter", "DcDoubleParameter") == binding
            and ResolveField(graph, binding, "rrOwnerFeature", "DcSketch") == owner
            and ResolveField(graph, binding, "rParentFeature", "DcSketch") == owner
            and ResolveField(graph, parameter, "dcParameter", "DcDoubleParameter") == binding
            and parameter.Fields["userName"] == role
            and parameter.Fields["isUserDefined"] is False,
            ORDER_ERROR,
        )
    expected = (*browser, *zip(DIMENSION_ROLES, dimensions, strict=True))
    actual = sorted(
        (node.Identity, subject.ObserverIndex)
        for node in graph.Nodes.values()
        for subject in node.Frame.Subjects or ()
        if (
            subject.Target == SegmentRef(settings.ObjectId, settings.SegmentId)
            or node.SegmentId == settings.SegmentId
            and subject.Target == LocalRef(settings.ObjectId)
        )
    )
    require(
        actual == sorted((node.Identity, rank) for rank, (_, node) in enumerate(expected)),
        ORDER_ERROR,
    )
    rows = [
        {"role": role, "id": node.Identity, "class": node.ClassName, "rank": rank}
        for rank, (role, node) in enumerate(expected)
    ]
    return {
        "settings_id": settings.Identity,
        "browser_observers": rows[:len(browser)],
        "dimension_observers": rows[len(browser):],
    }


def _coordinates(point):
    return point["x"], point["y"], point["z"]


def orient_sketch_lines(author):
    reference = author.Reference
    sketch_role = SketchRole(author)
    sketch = author.FindEntity(sketch_role)
    feature = author.FindEntity("dc_sketch")
    matrix = author.FindEntity("sketch_matrix")
    plane = author.FindEntity("sketch_plane")
    cache = author.FindEntity("plane_cache")
    frame = cache.FieldValues["rCachedGeometry"]
    require(
        cache.ClassName == "ETCachedPlane"
        and sketch.FieldValues["rDcNode"] == reference("dc_sketch")
        and feature.FieldValues["rSketchPlaneMatrix"] == reference("sketch_matrix")
        and matrix.FieldValues["dataRefs"] == [reference("sketch_plane")]
        and plane.FieldValues["caches"] == [reference("plane_cache")]
        and frame["normalReversed"] is False,
        FRAME_ERROR,
    )
    ux, uy, uz = _coordinates(frame["uAxis"])
    vx, vy, vz = _coordinates(frame["vAxis"])
    normal = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    lines = tuple(entity for entity in author.Entities if entity.ClassName == "Line3D")
    corners = tuple(author.FindEntity(role) for role in KCornerRoles)
    following = (*corners[1:], corners[0])
    pairs = tuple(zip(corners, following, strict=True))
    require(
        normal == (0.0, 0.0, 1.0)
        and tuple(line.RoleName for line in lines) == KLineRoles
        and all(
            line.ParentRole == sketch_role
            and line.FieldValues["rStartPoint"] == reference(start.RoleName)
            and line.FieldValues["rEndPoint"] == reference(end.RoleName)
            for line, (start, end) in zip(lines, pairs, strict=True)
        ),
        FRAME_ERROR,
    )
    endpoints = tuple(
        (_coordinates(start.FieldValues["point"]), _coordinates(end.FieldValues["point"]))
        for start, end in pairs
    )
    plane_z = _coordinates(frame["origin"])[2]
    require(
        all(start[2] == end[2] == plane_z for start, end in endpoints)
        and sum(start[0] * end[1] - start[1] * end[0] for start, end in endpoints) > 0,
        FRAME_ERROR,
    )
    for line in lines:
        author.Change(line.RoleName, planeNormal=MakePoint(*normal))
