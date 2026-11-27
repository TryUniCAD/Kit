# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# the source fixture must track every collector pin without staging unrelated automation files
KBossSources = (
    "RunSolidWorksBossWitness.py",
    "VerifySolidWorksBossWitness.py",
    "Records.py",
    "WindowsProcess.py",
    "WindowsApi.py",
    "WindowsJobMembers.py",
    "LogCapture.py",
    "ApplicationWorkers/ApplicationProtocol.py",
    "ApplicationWorkers/SolidWorksReadbackWorker.py",
    "ApplicationWorkers/SolidWorksProgress.py",
    "ApplicationWorkers/SolidWorksAvailability.py",
    "ApplicationWorkers/WindowsIdentity.py",
    "ApplicationWorkers/WindowsRecords.py",
    "CaptureTools/SolidWorksAuthoring/RunBossWitness.ps1",
    "CaptureTools/SolidWorksAuthoring/BossWitnessReadback.cs",
    "CaptureTools/SolidWorksAuthoring/P04Readback.cs",
    "CaptureTools/SolidWorksAuthoring/P02Readback.cs",
    "CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs",
)
