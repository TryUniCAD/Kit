# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
import sys
import time
import traceback

from CaptureTools.Catalogue.Fusion.BuildFusion import BuildFusion
from CaptureTools.Catalogue.Fusion.CheckFusion import CheckFusion
from CaptureTools.Catalogue.Fusion.FusionBatch import ModelCase
from CaptureTools.Catalogue.Fusion.FusionInputs import KFusionInputs, KFusionScope
from CaptureTools.Catalogue.Fusion.FusionReadback import CaptureReadback
from CaptureTools.Catalogue.Fusion.ReadFusionPlan import LoadFusionTool, ReadFusionBytes
from CaptureTools.Catalogue.Fusion.VerifyReport import VerifyReport


# separate native processes must be proven before fresh readback can reuse authored baselines
def PriorCapture(PlanPath, PlanHash, Plan, Fresh, Process):
    Directory = PlanPath.parent / "phase-a"
    Raw = ReadFusionBytes(Directory / "report.json", 16 * 1024 * 1024)
    Receipt = json.loads(ReadFusionBytes(Directory / "receipt.json", 1024 * 1024))
    Report = json.loads(Raw)
    VerifyReport(Receipt, Report, Raw, PlanHash, "a", Plan["cases"])
    Prior = Report["process"]
    if (
        Report["source_revision"] != Plan["source_revision"]
        or Report["pins"] != Plan["pins"]
        or Report["mode"] != Plan["mode"]
        or Prior["pid"] == Process["pid"]
        or Fresh["process_info"](Prior["pid"]) is not None
        or Process["start_unix_seconds"] <= Prior["start_unix_seconds"]
        or Process["start_unix_seconds"] <= Report["ended_unix_seconds"]
    ):
        raise RuntimeError(
            "fusion phase b requires the exact completed phase a and a fresh native process"
        )
    return Report


# native document ownership is registered before any builder operation can fail
def OwnDesignMut(Helper, Owned):
    Original = Helper["new_design"]

    # partial authoring failures must leave their documents visible to final cleanup
    def NewOwned(Application):
        Document = Application.documents.add(
            Helper["adsk"].core.DocumentTypes.FusionDesignDocumentType
        )
        if Document is None:
            raise RuntimeError("fusion did not create an owned design")
        Owned.append(Document)
        Design = Helper["design_of"](Document)
        Design.designType = Helper["adsk"].fusion.DesignTypes.ParametricDesignType
        Design.fusionUnitsManager.distanceDisplayUnits = Helper[
            "adsk"
        ].fusion.DistanceUnits.MillimeterDistanceUnits
        return Document, Design, Design.rootComponent

    Helper["new_design"] = NewOwned
    return Original


# local development workers author and measure requested geometry outside production conversion paths
def RunFusionPhase(PlanPath, PlanHash, Phase, Plan, Sources):
    if Phase not in ("a", "b") or sys.platform != "darwin":
        raise RuntimeError(
            "parameterized fusion native phases require an admitted macos fusion host"
        )
    Fresh = LoadFusionTool(KFusionInputs["fresh_process"], Sources["fresh_process"])
    Helper = LoadFusionTool(KFusionInputs["helper"], Sources["helper"])
    Bindings = LoadFusionTool(KFusionInputs["bindings"], Sources["bindings"])
    Helper["capture_sketch_bindings"] = Bindings["capture_sketch_bindings"]
    Application = Helper["adsk"].core.Application.get()
    if Application is None or Application.documents.count != 0:
        raise RuntimeError(
            "parameterized fusion capture requires an exclusive empty session"
        )
    Process = Fresh["process_info"](os.getpid())
    if Process is None:
        raise RuntimeError("fusion native process identity is unavailable")
    Prior = (
        PriorCapture(PlanPath, PlanHash, Plan, Fresh, Process) if Phase == "b" else None
    )
    if Prior is not None and Prior["application_build"] != Application.version:
        raise RuntimeError("fusion build changed between native phases")
    Output = PlanPath.parent / f"phase-{Phase}"
    Output.mkdir()
    Report = {
        "schema": 1,
        "scope": KFusionScope,
        "source_revision": Plan["source_revision"],
        "pins": Plan["pins"],
        "mode": Plan["mode"],
        "phase": Phase,
        "plan_sha256": PlanHash,
        "application": "fusion",
        "application_build": Application.version,
        "process": Process,
        "started_unix_seconds": time.time(),
        "cases": [],
        "errors": [],
    }
    if Prior is not None:
        Report["previous_process"] = Prior["process"]
        Report["previous_phase_report_sha256"] = Fresh["file_digest"](
            PlanPath.parent / "phase-a" / "report.json"
        )
    Owned = []
    Original = OwnDesignMut(Helper, Owned)
    try:
        Fresh["measure_control"](
            Helper,
            Application,
            Plan["pins"]["control"],
            Owned,
            Report,
            "healthy_control_before",
        )
        for Index, Case in enumerate(Plan["cases"]):
            Row = {"id": Case["id"], "case": ModelCase(Case)}
            Report["cases"].append(Row)
            try:
                if Phase == "a":
                    Document = BuildFusion(Helper, Application, ModelCase(Case))
                    Row["authored"] = CheckFusion(Helper, Document, ModelCase(Case))
                    Row["archive"] = Fresh["save_archive"](
                        Helper, Document, Output, f"{Case['id']}-baseline.f3d"
                    )
                    Helper["close"](Document, Owned)
                else:
                    Row.update(
                        CaptureReadback(
                            Helper,
                            Fresh,
                            Application,
                            Case,
                            Prior["cases"][Index],
                            Output,
                            Owned,
                        )
                    )
            except Exception:
                Row["diagnostic"] = traceback.format_exc()
                Report["errors"].append(Case["id"])
            finally:
                for Document in list(Owned):
                    Helper["close"](Document, Owned)
        Fresh["measure_control"](
            Helper,
            Application,
            Plan["pins"]["control"],
            Owned,
            Report,
            "healthy_control_after",
        )
    except Exception:
        Report["errors"].append(traceback.format_exc())
    finally:
        try:
            for Document in list(Owned):
                Helper["close"](Document, Owned)
            if Application.documents.count != 0:
                raise RuntimeError(
                    "fusion retained a document outside the owned capture"
                )
        except Exception:
            Report["errors"].append(traceback.format_exc())
        Helper["new_design"] = Original
        Report["ended_unix_seconds"] = time.time()
        Report["status"] = "failed" if Report["errors"] else "complete"
        ReportHash = Fresh["write_json"](Output / "report.json", Report)
        Fresh["write_json"](
            Output / "receipt.json",
            {
                "schema": 1,
                "scope": KFusionScope,
                "phase": Phase,
                "status": Report["status"],
                "plan_sha256": PlanHash,
                "report_sha256": ReportHash,
            },
        )
    if Report["errors"]:
        raise RuntimeError(
            f"parameterized fusion capture failed read {Output / 'report.json'}"
        )
    return Report
