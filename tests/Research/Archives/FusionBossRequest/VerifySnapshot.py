# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from io import BytesIO
from zipfile import ZipFile

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.EmitPrismSnap import (
    EmitPrismSnap,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

from tests.Research.Archives.FusionBossRequest.CheckSnapshotOwn import CheckSnapOwners


# the raw snapshot payload must represent the same authored prism and tagged sketch outlines
def VerifySnapshot(
    ArchiveBytes: bytes,
    Model: DocumentModel,
    Graph: NativeGraph,
    Context: ExtrudeContext,
) -> dict[str, object]:
    (Entry,) = Model.Snapshots
    Snapshot = Entry.Snapshot
    History = Model.Bodies[0].History
    assert isinstance(Snapshot, PrismSnapshot) and isinstance(History, PrismHistory)
    assert Snapshot.Model == History.Model and Snapshot.Frame == History.Frame
    assert Snapshot.TagSet == History.TagSet and Snapshot.Stamp == History.Stamp
    assert Snapshot.Header.RootCount == 4 and Snapshot.Header.IntWidth == 8
    for Region in (Snapshot.Profile, Snapshot.Sketch):
        assert set(Region.CornersCm) == set(History.Frame.CornersCm[:4])
        assert len(Region.Edges) == 4
    Roots = CheckSnapOwners(Graph, Context, Model.Asset.AssetId, Entry.Name)
    with ZipFile(BytesIO(ArchiveBytes)) as Archive:
        WireValue = Archive.read(KAssetPrefix + Entry.Name)
    assert WireValue == EmitPrismSnap(Snapshot)
    return {
        "member": Entry.Name,
        "member_sha256": HashBytes(WireValue).hexdigest(),
        "int_width": Snapshot.Header.IntWidth,
        "root_ids": dict(
            zip(("tool_solid", "profile_region", "sketch_sheet"), Roots, strict=True)
        ),
        "native_cache_addresses": "zero_reset_unmeasured",
    }
