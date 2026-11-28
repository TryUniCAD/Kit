# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Build ordinary standalone exchange records from the authored system graph."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ExchangePack import ExchangeValue, OrderedMap, PackExchange
from OrdinaryResolved import ResolvedSystem
from PartFeatureIndex import KConfiguration
from PartFraming import VersionStorage
from PrincipalPlaneView import KPrincipalFrames, PrincipalFrame
from ResolvedFolders import SystemFolder
from ResolvedPrincipal import KPlaneClass, KPlaneNames, PrincipalPlane
from UnqlitePage import WriteSingleBucket
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KObjectDb = "Contents/3DExperienceExchange2"
KSelection = "moSelectionSetFolder_c"
KIndexKey = b"TOC"
KIdentity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
KOrigin = (0.0, 0.0, 0.0)


# each exchange key holds a distinct caller-issued identity in the new document
@dataclass(frozen=True, slots=True)
class ObjectExchange:
    Folder: UUID
    Planes: tuple[UUID, UUID, UUID]
    Document: UUID
    Created: datetime
    IndexOrder: tuple[int, int, int] = (0, 1, 2)


# the same ordered properties are visible through both native feature owners
def SelectionRecord(Folder: SystemFolder) -> OrderedMap:
    return SelectionFields(Folder.Name, Folder.TreeId, Folder.Feature.UpdateStamp)


def SelectionFields(Name: str, TreeId: int, Stamp: int) -> OrderedMap:
    return OrderedMap(
        (
            ("NumSelectionSets", 0),
            ("class", KSelection),
            ("class", KSelection),
            ("description", Name),
            ("hidden", 0),
            ("hidden", False),
            ("id", TreeId),
            ("name", Name),
            ("suppressed", 0),
            ("suppressed", False),
            ("updatestamp", Stamp),
            ("updatestamp", Stamp),
        )
    )


# exchange matrices transpose the native datum basis and retain signed zero
def ExchangeTransform(
    Basis: tuple[float, ...], Offset: tuple[float, float, float]
) -> OrderedMap:
    Matrix = tuple(Basis[Row + 3 * Column] for Row in range(3) for Column in range(3))
    return OrderedMap((("class", "mgXform_c"), ("elems", (*Matrix, *Offset, 1.0))))


# ordinary exchange datums describe the same origin and normals as the resolved graph
def DatumRecord(Plane: PrincipalPlane, Frame: PrincipalFrame) -> OrderedMap:
    Basis = KIdentity if Frame.Basis is None else Frame.Basis
    return DatumFields(
        Plane.Name,
        Plane.TreeId,
        Plane.Feature.UpdateStamp,
        Frame.Normal,
        KOrigin,
        Basis,
        KOrigin,
    )


def DatumFields(
    Name: str,
    TreeId: int,
    Stamp: int,
    Normal: tuple[float, float, float],
    Origin: tuple[float, float, float],
    Basis: tuple[float, ...],
    Offset: tuple[float, float, float],
) -> OrderedMap:
    return OrderedMap(
        (
            ("class", KPlaneClass),
            ("class", KPlaneClass),
            ("description", Name),
            ("hidden", 0),
            ("hidden", True),
            ("id", TreeId),
            ("name", Name),
            ("normal", Normal),
            ("point", Origin),
            ("subtype", "swRefPlaneSWStandard"),
            ("suppressed", 0),
            ("suppressed", False),
            ("transform", ExchangeTransform(Basis, Offset)),
            ("updatestamp", Stamp),
            ("updatestamp", Stamp),
        )
    )


# the table of contents refers back to the actual keys in the same database
def ObjectReference(Key: UUID) -> tuple[str, ExchangeValue]:
    return ("object", OrderedMap((("class", "object"), ("guid", str(Key)))))


# the index retains both groups and never substitutes positional record identities
def ExchangeToc(Keys: ObjectExchange) -> OrderedMap:
    Selection = OrderedMap((("class", KSelection), ObjectReference(Keys.Folder)))
    Planes = OrderedMap(
        (
            ("class", KPlaneClass),
            *(ObjectReference(Keys.Planes[Slot]) for Slot in Keys.IndexOrder),
        )
    )
    Model = OrderedMap(
        (
            ("class", "moPart_c"),
            ("configid", 0),
            ("configname", KConfiguration),
            ("object", Selection),
            ("object", Planes),
        )
    )
    return OrderedMap((("class", "object-map"), ("model", Model)))


# fresh ordinary standalone documents have the measured desktop exchange flags
def ExchangeDocument(ClassName: str) -> OrderedMap:
    return OrderedMap(
        (
            ("ModelDocFrozen", False),
            ("RenameTitleAsPP", True),
            ("SaveAsNewCalled", False),
            ("class", ClassName),
            ("platformflag", 2),
            ("repairDTForDefaultConfigflag", False),
            ("useEnglishDescriptionForWeldmentCutList", False),
        )
    )


# build the records using matching resolved feature names and saved update clocks
def ExchangeRecords(
    Generation: int, Keys: ObjectExchange, System: ResolvedSystem
) -> tuple[tuple[bytes, bytes], ...]:
    VersionStorage(Generation)
    Identities = (Keys.Folder, *Keys.Planes, Keys.Document)
    RequireArch(
        len(set(Identities)) == len(Identities) == 5
        and all(Key.version == 4 for Key in Identities),
        True,
        "independent exchange object identities",
    )
    RequireArch(
        tuple(sorted(Keys.IndexOrder)),
        (0, 1, 2),
        "one reference to each principal datum",
    )
    (Folder,) = (Folder for Folder in System.Folders if Folder.TreeId == 25)
    RequireArch(Folder.Name, "Selection Sets", "ordinary empty selection folder")
    RequireArch(
        tuple((Plane.Name, Plane.TreeId) for Plane in System.Planes),
        tuple(zip(KPlaneNames, (2, 3, 4), strict=True)),
        "ordinary exchange datum order",
    )
    Records = (
        (str(Keys.Folder).encode("ascii"), SelectionRecord(Folder)),
        *(
            (str(Key).encode("ascii"), DatumRecord(Plane, Frame))
            for Key, Plane, Frame in zip(
                Keys.Planes, System.Planes, KPrincipalFrames, strict=True
            )
        ),
        (KIndexKey, ExchangeToc(Keys)),
        (str(Keys.Document).encode("ascii"), ExchangeDocument("uiPartDoc_c")),
    )
    return tuple((Key, PackExchange(Value)) for Key, Value in Records)


# a new database retains the live records and has an empty free-space tail
def EncodeObjectExchangeDb(
    Generation: int, Keys: ObjectExchange, System: ResolvedSystem
) -> bytes:
    return WriteSingleBucket(Keys.Created, ExchangeRecords(Generation, Keys, System))
