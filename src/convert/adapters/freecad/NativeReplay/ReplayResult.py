# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.freecad.NativeReplay.ReplayTransfers import ReplayTransfers
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordDiagnostic import Diagnostic


# byte preservation and reconstruction support require independent outcome evidence
def ReplayResult(
    AdapterId: str,
    Document: CadDocument,
    OutputPath: FilePath | None,
    ByteCount: int,
    HasOuterRefs: bool,
    Transfers: tuple[CapTransfer, ...],
    UnprovenFeatures: tuple[str, ...],
) -> WriteResult:
    CanRebuild = not UnprovenFeatures
    Diagnostics = Document.diagnostics
    if UnprovenFeatures:
        Diagnostics += (
            Diagnostic(
                "freecad.native_replay.unqualified",
                "Exact native bytes are preserved without editable feature qualification",
                attributes={"unsupported_features": UnprovenFeatures},
            ),
        )
    return WriteResult(
        path=OutputPath,
        adapter=AdapterId,
        bytes_written=ByteCount,
        diagnostics=Diagnostics,
        transfers=ReplayTransfers(Transfers, CanRebuild),
        metadata={
            "mode": "exact_native_roundtrip",
            "compatibility": "native-exact",
            "vendor_loadable": CanRebuild,
            "application_usable": CanRebuild,
            **({"unsupported_features": UnprovenFeatures} if UnprovenFeatures else {}),
            "native_self_contained": not HasOuterRefs,
            "referenced_files_written": 0,
            "runtime": "python-stdlib",
        },
        requirements=("referenced FreeCAD component files",) if HasOuterRefs else (),
        application_usable=CanRebuild,
        vendor_loadable=CanRebuild,
    )
