# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from Corpus import git


# queued native execution must use the same immutable source that its controller job names
def CheckSolidSrc(Revision):
    SourceRoot = Path(__file__).resolve().parents[4]
    Selected = [
        SourceRoot / "re/automation/InferenceGrid/Authoring/SolidWorker.py",
        SourceRoot / "re/automation/InferenceGrid/Authoring/SolidSources.py",
        SourceRoot
        / "re/automation/CaptureTools/SolidWorksAuthoring/SolidWorksCapture.cs",
        SourceRoot / "re/automation/PairSpecs.json",
        SourceRoot / "re/solidworks/examples/.SLDPRT/example.SLDPRT",
    ]
    Selected.extend(
        FileValue
        for FileValue in (
            SourceRoot / "re/automation/CaptureTools/Catalogue/SolidWorks"
        ).iterdir()
        if FileValue.suffix in {".py", ".cs", ".ps1"}
    )
    for SourcePath in Selected:
        Relative = SourcePath.relative_to(SourceRoot).as_posix()
        if SourcePath.is_symlink() or SourcePath.read_bytes() != git(
            SourceRoot, "show", Revision + ":" + Relative
        ):
            raise ValueError(
                "SOLIDWORKS authoring source differs from its scheduled revision"
            )
