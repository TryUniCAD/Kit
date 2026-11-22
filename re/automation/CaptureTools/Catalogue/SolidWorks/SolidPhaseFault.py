# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path


# persisted worker failures must retain the native cause after temporary sessions are removed
def SolidPhaseFault(OutputPath, PhaseName, ExitCode):
    Evidence = []
    for Suffix in (".log", "-owner.json", "-native.json", ".stderr.log"):
        FilePath = Path(OutputPath) / (PhaseName + Suffix)
        if FilePath.is_file() and not FilePath.is_symlink():
            with FilePath.open("rb") as Stream:
                Stream.seek(0, 2)
                Stream.seek(max(0, Stream.tell() - 12000))
                Content = Stream.read(12000).decode("utf-8", errors="replace").strip()
            if Content:
                Evidence.append(FilePath.name + ":\n" + Content)
    return RuntimeError(
        "SOLIDWORKS authoring phase failed inspect "
        + str(Path(OutputPath) / (PhaseName + ".stderr.log"))
        + "\nexit "
        + str(ExitCode)
        + "\n"
        + "\n".join(Evidence)
    )
