# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from struct import error as StructError

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.CircleOnly.BuildSketch import BuildSoloDoc
from convert.adapters.solidworks.Core.CircleOnly.Candidate import IsCircleOnly
from convert.adapters.solidworks.Resolved.Circular.ReadCircleOnly import ReadCircleOnly
from interchange.document.Models.DocumentModel import CadDocument
from convert.adapters.solidworks.Core.Native import NativeModel
from interchange.Enums.EnumDocument import Severity
from interchange.Records.RecordDiagnostic import Diagnostic


# complete configuration and feature history must prove that the fallback body has no owner
def ProjectSoloDoc(
    Document: CadDocument, Model: NativeModel, Archive: SldprtArchive
) -> CadDocument:
    ConfigId = Model.active_configuration_id
    if ConfigId is None:
        return Document
    Config = f"Contents/Config-{ConfigId}"
    Stream = f"{Config}-ResolvedFeatures"
    if (
        not IsCircleOnly(Document, Model, Stream)
        or ContainerMo(Archive.streams) != KConfigGen
    ):
        return Document
    try:
        Saved = ReadCircleOnly(
            Archive.require(Config), Archive.require(Stream), KConfigGen
        )
        RequireArch(
            Document.brep is None or not Document.brep.bodies,
            True,
            "standalone circular history conflicts with decoded body geometry",
        )
        return BuildSoloDoc(Document, Saved, Stream)
    except (KeyError, IndexError, ValueError, StructError) as ErrorInfo:
        return Replace(
            Document,
            diagnostics=(
                *Document.diagnostics,
                Diagnostic(
                    code="sldprt.circular_sketch_unresolved",
                    message=str(ErrorInfo),
                    severity=Severity.INFO,
                ),
            ),
        )
