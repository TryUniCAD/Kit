# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from re import fullmatch
import subprocess
import sys

# native workers may load this tool before the research package is available
REPO = Path(__file__).resolve().parents[5]

# every helper is admitted before research imports are enabled in the native process
PINS = {
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

# distinct scope prevents fixed historical recipes from accepting new parameter grids
SCOPE = "catalogue-parametric-fusion"


# native execution consumes only committed local inputs with exact immutable identities
def CapturePins(Revision):
    Pins = {}
    for RoleName, Relative in PINS.items():
        Target = REPO / Relative
        if (
            Target.is_symlink()
            or not Target.is_file()
            or not Target.resolve().is_relative_to(REPO)
        ):
            raise ValueError(
                f"fusion capture input must be a regular owned file {Relative}"
            )
        Committed = subprocess.check_output(
            [
                "git",
                "--no-replace-objects",
                "-C",
                str(REPO),
                "show",
                f"{Revision}:{Relative}",
            ]
        )
        if len(Committed) > 64 * 1024 * 1024 or Target.read_bytes() != Committed:
            raise ValueError(
                f"fusion capture input differs from the reviewed revision {Relative}"
            )
        Pins[RoleName] = {
            "path": Relative,
            "size_bytes": len(Committed),
            "sha256": sha256(Committed).hexdigest(),
        }
    return Pins


# preparation can be automated without importing the vendor or opening an application
def prepare(Output, Cases, Mode="discovery"):
    Output = Path(Output).resolve()
    if Output.exists() or Output.is_relative_to(REPO):
        raise ValueError(
            "choose a new fusion capture output directory outside the checkout"
        )
    Revision = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "-C",
            str(REPO),
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ],
        text=True,
    ).strip()
    Pins = CapturePins(Revision)
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.FusionBatch import NormalizeCases

    Normal = NormalizeCases(Cases, Mode)
    Plan = {
        "schema": 1,
        "scope": SCOPE,
        "source_revision": Revision,
        "pins": Pins,
        "cases": Normal,
        "mode": Mode,
    }
    Raw = (json.dumps(Plan, sort_keys=True, indent=2, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    PlanHash = sha256(Raw).hexdigest()
    Output.mkdir(mode=0o700)
    with (Output / "plan.json").open("xb") as Stream:
        Stream.write(Raw)
        Stream.flush()
        os.fsync(Stream.fileno())
    return {
        "run_directory": str(Output),
        "source_revision": Revision,
        "plan_sha256": PlanHash,
        "cases": Normal,
        "mode": Mode,
        "scope": SCOPE,
    }


# runtime imports remain disabled until every executable input matches its prepared pin
def VerifyInputs(PlanPath, PlanHash):
    if PlanPath.is_symlink() or not PlanPath.is_file():
        raise ValueError("fusion capture plan must be a regular input")
    with PlanPath.open("rb") as Stream:
        Raw = Stream.read(4 * 1024 * 1024 + 1)
    if len(Raw) > 4 * 1024 * 1024 or sha256(Raw).hexdigest() != PlanHash:
        raise ValueError("prepared fusion plan changed or exceeds its byte limit")
    Plan = json.loads(Raw)
    VerifySources(Plan)


# embedded workers admit every module before making the research package importable
def VerifySources(Plan):
    if (
        not isinstance(Plan, dict)
        or set(Plan) != {"schema", "scope", "source_revision", "pins", "cases", "mode"}
        or type(Plan["schema"]) is not int
        or Plan["schema"] != 1
        or Plan["scope"] != SCOPE
        or not isinstance(Plan["source_revision"], str)
        or not fullmatch("[0-9a-f]{40}", Plan["source_revision"])
        or not isinstance(Plan["pins"], dict)
        or set(Plan["pins"]) != set(PINS)
    ):
        raise ValueError("fusion capture executable dependency roster changed")
    for RoleName, Relative in PINS.items():
        Pin = Plan["pins"][RoleName]
        Target = REPO / Relative
        if (
            not isinstance(Pin, dict)
            or set(Pin) != {"path", "size_bytes", "sha256"}
            or Pin["path"] != Relative
            or Target.is_symlink()
            or not Target.is_file()
            or not Target.resolve().is_relative_to(REPO)
        ):
            raise ValueError("fusion capture executable dependency path changed")
        with Target.open("rb") as Stream:
            Content = Stream.read(64 * 1024 * 1024 + 1)
        if (
            len(Content) > 64 * 1024 * 1024
            or len(Content) != Pin["size_bytes"]
            or sha256(Content).hexdigest() != Pin["sha256"]
        ):
            raise ValueError(f"fusion capture executable dependency changed {Relative}")


# native worker admission validates case identities without depending on embedded search paths
def ValidatePlan(Plan):
    VerifySources(Plan)
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.FusionBatch import NormalizeCases

    Normal = NormalizeCases(Plan["cases"], Plan["mode"])
    if Normal != Plan["cases"]:
        raise ValueError("fusion prepared case roster is not canonical")
    return Normal


# counterpart workers derive exact artifact roles after their source admission checks
def PhasePaths(Plan, Phase):
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.FusionBatch import PhasePaths as ReadPaths

    return ReadPaths(Plan, Phase)


# native intake reuses independently derived geometry comparisons after pinned source admission
def VerifyReport(Receipt, Report, Raw, PlanHash, Phase, Cases):
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.VerifyReport import VerifyReport as CheckReport

    return CheckReport(Receipt, Report, Raw, PlanHash, Phase, Cases)


# accepted native files must bind every baseline and edit to their immutable output role
def CheckArtifacts(Report, Files, Phase):
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.VerifyReport import CheckArtifacts as VerifyFiles

    return VerifyFiles(Report, Files, Phase)


# existing application workers invoke the exact prepared tool after admission and restart fencing
def run_phase(PlanPath, PlanHash, Phase):
    VerifyInputs(Path(PlanPath), PlanHash)
    sys.path.insert(0, str(REPO / "re/automation"))
    from CaptureTools.Catalogue.Fusion.ReadFusionPlan import ReadFusionPlan

    Plan, Sources = ReadFusionPlan(Path(PlanPath), PlanHash)
    from CaptureTools.Catalogue.Fusion.FusionPhase import RunFusionPhase

    return RunFusionPhase(Path(PlanPath), PlanHash, Phase, Plan, Sources)


# a process entry point exposes planning and refusal without requiring native application imports
def MainCapture():
    Parser = argparse.ArgumentParser(
        description="Prepare bounded parameterized Fusion authoring and fresh process verification"
    )
    Parser.add_argument("--output", required=True, type=Path)
    Parser.add_argument("--cases", required=True, type=Path)
    Parser.add_argument(
        "--mode", choices=("discovery", "qualification", "holdout"), default="discovery"
    )
    Arguments = Parser.parse_args()
    try:
        Raw = Arguments.cases.read_bytes()
        if len(Raw) > 1024 * 1024:
            raise ValueError("fusion case request exceeds its byte limit")
        Result = prepare(Arguments.output, json.loads(Raw), Arguments.mode)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ) as Error:
        Parser.exit(1, f"fusion capture preparation refused: {Error}\n")
    print(json.dumps(Result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    MainCapture()
