# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.Circular.CircleOnly import CircleOnly
from convert.adapters.solidworks.Resolved.Circular.CircleOnlyTail import ReadOnlyTail
from convert.adapters.solidworks.Resolved.Circular.Profile import ReadRoundRegion
from convert.adapters.solidworks.Resolved.Circular.Records import CircularSupport
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.Resolved.RectanglePart import ResolveDatum
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
from convert.adapters.solidworks.Sketch.CircularDisplay import ReadRadialView
from convert.adapters.solidworks.Sketch.CircularMembers import (
    CircularCursor,
    ReadCircle,
    ReadDiameter,
    ReadOriginJoin,
    ReadPoints,
    ReadViewPrefix,
)
from convert.adapters.solidworks.Sketch.CircularRecords import CircularHeader


# a standalone circle is qualified only after the whole saved profile reaches its footer
def ReadCircleOnly(ConfigData: bytes, Resolved: bytes, Generation: int) -> CircleOnly:
    ConfigMap, MapWalk = ReadOrdinaryMap(ConfigData, Generation)
    RequireArch(
        MapWalk["atom_count"], 0, "standalone circular configuration has no body atoms"
    )
    RequireArch(
        bool(MapWalk["regions"]),
        False,
        "standalone circular configuration has no body regions",
    )
    Parent = OpenResolved(Resolved, ConfigMap, 18)
    System = ReadSysPrefix(Parent)
    Origin = ReadOrigin(Parent, Generation)
    RequireArch(
        Origin.Support.FeatureId, System.Planes[0].FeatureId, "typed Origin datum"
    )
    StartOffset = Parent.Offset
    _, _, FeatureObject = Parent.TakePointer(("moProfileFeature_c",), KDefinitionKind)
    _ = Parent.TakePointer(("moNodeName_c",), KClassRefKind)
    NameValue, FeatureId, _ = ReadProfileHead(Parent, (0x40000000, 0xC0000000))
    _, _, SketchObject = Parent.TakePointer(("sgSketch",), KClassRefKind)
    Profile: CircularHeader = {
        "name": NameValue,
        "feature_id": FeatureId,
        "feature_node": FeatureObject,
        "feature_start": StartOffset,
        "sketch_node": SketchObject,
    }
    Cursor = CircularCursor(Parent)
    Points = ReadPoints(Cursor)
    Circle = ReadCircle(Cursor, Points)
    Diameter = ReadDiameter(Cursor, Circle)
    Coincidence = ReadOriginJoin(Cursor, Points, Circle, Origin)
    Prefix = ReadViewPrefix(Cursor)
    Display = ReadRadialView(Cursor, Profile, Diameter)
    _ = ReadRoundRegion(Cursor, Circle)
    _ = ReadChainState(Cursor, False, (Circle["native_id"],))
    Reference = ReadProfileRef(Cursor, Generation)
    Datum, Directions = ResolveDatum(Reference, System.Planes)
    Support: CircularSupport = {
        "span": [Reference.Offset, Cursor.Offset],
        "feature": Reference.FeatureId,
        "axes": Directions,
    }
    StateWord = ReadOnlyTail(Cursor, Profile, Circle)
    return CircleOnly(
        Profile,
        Datum,
        Origin,
        Points,
        Circle,
        Diameter,
        Coincidence,
        {**Prefix, **Display},
        Support,
        Reference,
        StateWord,
        Cursor.Offset,
    )
