# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from Corpus import git

# native claims must include nested builders and their shared recipe compiler rather than only entry scripts
KSourceFolders = (
    "re/automation/InferenceGrid/Authoring",
    "re/automation/CaptureTools/Catalogue/SolidWorks",
    "re/automation/CaptureTools/Catalogue/Recipes",
)

# these native inputs and recipe definitions are dependencies outside the executable builder folders
KSourceFiles = (
    "re/automation/CaptureTools/SolidWorksAuthoring/SolidWorksCapture.cs",
    "re/automation/PairSpecs.json",
    "re/automation/FeatureRecipeSpecs.json",
    "re/automation/InferenceGrid/FeatureSpecs.py",
    "re/automation/Corpus.py",
    "re/automation/Evidence.py",
    "re/automation/Records.py",
    "re/automation/InferenceInputs.py",
    "re/automation/InferenceSession.py",
    "re/automation/Sessions.py",
    "re/automation/Processes.py",
    "re/automation/LogCapture.py",
    "re/automation/LinuxOomProof.py",
    "re/automation/OutputManifest.py",
    "re/automation/Runners.py",
    "re/solidworks/examples/.SLDPRT/example.SLDPRT",
)


# tracked removals and untracked executable additions must both invalidate a queued source identity
def SolidSourceSet(SourceRoot, Revision):
    Expected = (
        git(SourceRoot, "ls-tree", "-r", "--name-only", Revision, "--", *KSourceFolders)
        .decode("utf-8")
        .splitlines()
    )
    Selected = set(KSourceFiles)
    Selected.update(
        Relative
        for Relative in Expected
        if Path(Relative).suffix in {".py", ".cs", ".ps1", ".json"}
    )
    for Folder in KSourceFolders:
        Selected.update(
            FilePath.relative_to(SourceRoot).as_posix()
            for FilePath in (SourceRoot / Folder).rglob("*")
            if FilePath.suffix in {".py", ".cs", ".ps1", ".json"}
        )
    return sorted(Selected)
