# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

# native scripts must use the same source tree whose evidence the controller admitted
KFusionRoot = Path(__file__).resolve().parents[5]

# each executable dependency remains pinned separately from sealed historical capture sources
KFusionInputs = {
    "tool": "re/automation/CaptureTools/Catalogue/Fusion/CaptureFusion.py",
    "batch": "re/automation/CaptureTools/Catalogue/Fusion/FusionBatch.py",
    "cases": "re/automation/CaptureTools/Catalogue/Fusion/FusionCases.py",
    "parameters": "re/automation/CaptureTools/Catalogue/Fusion/FusionParams.py",
    "expected": "re/automation/CaptureTools/Catalogue/Fusion/FusionExpected.py",
    "builder": "re/automation/CaptureTools/Catalogue/Fusion/BuildFusion.py",
    "check": "re/automation/CaptureTools/Catalogue/Fusion/CheckFusion.py",
    "reading": "re/automation/CaptureTools/Catalogue/Fusion/CheckReading.py",
    "sketch": "re/automation/CaptureTools/Catalogue/Fusion/FusionSketch.py",
    "inputs": "re/automation/CaptureTools/Catalogue/Fusion/FusionInputs.py",
    "plan": "re/automation/CaptureTools/Catalogue/Fusion/ReadFusionPlan.py",
    "phase": "re/automation/CaptureTools/Catalogue/Fusion/FusionPhase.py",
    "readback": "re/automation/CaptureTools/Catalogue/Fusion/FusionReadback.py",
    "edits": "re/automation/CaptureTools/Catalogue/Fusion/FusionEdits.py",
    "verify": "re/automation/CaptureTools/Catalogue/Fusion/VerifyReport.py",
    "helper": "re/automation/PairedCaptures/FusionCapture.py",
    "bindings": "re/automation/PairedCaptures/FusionBindings.py",
    "fresh_process": "re/automation/PairedCaptures/FusionFreshProcess.py",
    "control": "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
}

# scope separation prevents ordinary fixed capture receipts from admitting parameterized cases
KFusionScope = "catalogue-parametric-fusion"
