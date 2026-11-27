# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile


# each verified case retains its own bounded native bundle so decoder dependencies cannot exchange samples
def PackNative(WorkPath, ReportValue, FileName="Samples.zip"):
    if Path(FileName).name != FileName or "\\" in FileName:
        raise ValueError("native bundle must use a local artifact filename")
    Archives = ReportValue["archives"]
    if (
        not 1 <= len(Archives) <= 48
        or sum(Archive["size_bytes"] for Archive in Archives) > 256 * 1024 * 1024
    ):
        raise ValueError(
            "native capture archive roster exceeds its bounded decoder input"
        )
    BundlePath = WorkPath / FileName
    Manifest = {}
    with ZipFile(BundlePath, "x", compression=ZIP_STORED) as BundleFile:
        for Archive in Archives:
            SourcePath = Path(Archive["path"])
            SourceRaw = SourcePath.read_bytes()
            NativeName = SourcePath.name
            if NativeName in Manifest or len(SourceRaw) > 64 * 1024 * 1024:
                raise ValueError("duplicate or oversized native capture archive")
            SourceHash = sha256(SourceRaw).hexdigest()
            if (
                SourceHash != Archive["sha256"]
                or len(SourceRaw) != Archive["size_bytes"]
            ):
                raise ValueError("native sample changed before controller publication")
            BundleFile.writestr(NativeName, SourceRaw)
            Manifest[NativeName] = {
                "sha256": SourceHash,
                "size_bytes": len(SourceRaw),
            }
    return BundlePath, Manifest
