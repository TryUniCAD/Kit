# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from os import environ
from pathlib import Path
from sys import platform

from CaptureTools.Catalogue.SolidWorks.NativeSolidEnv import NativeSolidEnv
from CaptureTools.Catalogue.SolidWorks.SolidPhaseFault import SolidPhaseFault
from InferenceGrid.BuilderDevelopment.NativePlane.PlaneInputs import (
    CheckPlaneProgram,
    PlaneCases,
    PlaneSource,
    PlaneSourcePins,
)
from Records import canonical, digest


# existing Windows job ownership and timeouts bound the trusted collector and native descendants
def RunPlanePhase(Manifest, Output, Host, Phase, CandidateSourcePin):
    from WindowsProcess import WindowsProcess

    Root = Path(__file__).resolve().parents[5]
    Shell = (
        Path(environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    Command = [
        str(Shell),
        "-NoProfile",
        "-NonInteractive",
        "-STA",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(Path(__file__).with_name("RunPlane.ps1")),
        "-CasePath",
        str(Manifest),
        "-OutputDirectory",
        str(Output),
        "-InteropAssembly",
        Host["interop_assembly"],
        "-ExecutablePath",
        Host["executable"],
        "-CandidateSha256",
        CandidateSourcePin,
        "-Phase",
        Phase,
    ]
    with (
        (Output / (Phase + ".log")).open("xb") as Log,
        (Output / (Phase + ".stderr.log")).open("xb") as Errors,
    ):
        Process = WindowsProcess(
            Command, Root, NativeSolidEnv(Host), Log.fileno(), Errors.fileno()
        )
        try:
            ExitCode = Process.wait(timeout=Host.get("phase_seconds", 600))
            Process.finish()
            if ExitCode:
                Log.flush()
                Errors.flush()
                raise SolidPhaseFault(Output, Phase, ExitCode)
        finally:
            Process.close()


# raw observations are returned for an independent frozen verifier rather than self qualifying a builder
def RunPlaneCases(Program, Cases, Output, Host):
    if platform != "win32":
        raise ValueError(
            "native plane collector requires a licensed Windows SOLIDWORKS host"
        )
    Program = CheckPlaneProgram(Program)
    Cases = PlaneCases(Cases)
    if (
        not isinstance(Host, dict)
        or not {"executable", "interop_assembly"} <= Host.keys()
        or Host.keys()
        - {"executable", "interop_assembly", "native_environment", "phase_seconds"}
        or type(Host.get("phase_seconds", 600)) is not int
        or not 1 <= Host.get("phase_seconds", 600) <= 3600
    ):
        raise ValueError("invalid native plane host configuration")
    for Name in ("executable", "interop_assembly"):
        if not Path(Host[Name]).is_absolute() or not Path(Host[Name]).is_file():
            raise ValueError("native plane host capability is unavailable: " + Name)
    Root = Path(__file__).resolve().parents[5]
    Output = Path(Output).resolve()
    if Output.exists() or Output.is_relative_to(Root):
        raise ValueError(
            "native plane execution needs a new directory outside the source checkout"
        )
    Revision, Pins = PlaneSourcePins(Root)
    Control = Root / "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    if Control.is_symlink() or not Control.is_file():
        raise ValueError("native verification prerequisite control is unavailable")
    ControlPin = sha256(Control.read_bytes()).hexdigest()
    for Case in Cases:
        if (
            len(str(Output / ("C" + Case["id"]) / "A.SLDPRT").encode("utf-16-le")) // 2
            >= 260
        ):
            raise ValueError("native plane capture path exceeds the application limit")
    Output.mkdir(parents=True)
    Manifest = Output / "PlaneManifest.json"
    Manifest.write_text(
        canonical({"schema_version": 1, "program": Program, "cases": Cases}) + "\n",
        encoding="utf-8",
    )
    ManifestPin = sha256(Manifest.read_bytes()).hexdigest()
    Source = Output / "CandidateProgram.cs"
    Source.write_text(PlaneSource(Program), encoding="utf-8")
    CandidateSourcePin = sha256(Source.read_bytes()).hexdigest()
    for Phase in ("first", "second"):
        RunPlanePhase(Manifest, Output, Host, Phase, CandidateSourcePin)
        if sha256(Manifest.read_bytes()).hexdigest() != ManifestPin:
            raise ValueError("native candidate manifest changed during execution")
    _, After = PlaneSourcePins(Root)
    if (
        Pins != After
        or sha256(Control.read_bytes()).hexdigest() != ControlPin
        or sha256(Source.read_bytes()).hexdigest() != CandidateSourcePin
    ):
        raise ValueError("native capture changed a source or control input")
    Reports = []
    Archives = []
    for Case in Cases:
        Directory = Output / ("C" + Case["id"])
        Report = loads((Directory / "measurements.json").read_text(encoding="utf-8"))
        Reports.append(Report)
        for Saved in Report["saves"]:
            File = Directory / Saved["file"]
            if (
                File.is_symlink()
                or not File.is_file()
                or sha256(File.read_bytes()).hexdigest() != Saved["sha256"]
            ):
                raise ValueError("native candidate archive changed before return")
            Archives.append(
                {
                    **Saved,
                    "file": File.relative_to(Output).as_posix(),
                    "case_id": Case["id"],
                }
            )
    Controls = {
        Phase: loads((Output / (Phase + "-controls.json")).read_text(encoding="utf-8"))
        for Phase in ("first", "second")
    }
    Phases = {
        Phase: {
            Name: loads(
                (Output / (Phase + "-" + Name + ".json")).read_text(encoding="utf-8")
            )
            for Name in ("owner", "native")
        }
        for Phase in ("first", "second")
    }
    return {
        "schema_version": 1,
        "output_directory": str(Output),
        "source_revision": Revision,
        "program_sha256": digest(Program),
        "source_pins": Pins,
        "candidate_source": {
            "path": str(Source),
            "sha256": sha256(Source.read_bytes()).hexdigest(),
            "executed": True,
        },
        "manifest_sha256": ManifestPin,
        "application": {
            "name": "SOLIDWORKS",
            "build": Controls["first"]["application_build"],
            "executable_file_version": Reports[0]["executable_file_version"],
        },
        "cases": Reports,
        "controls": Controls,
        "phases": Phases,
        "archives": Archives,
        "control_sha256": ControlPin,
    }
