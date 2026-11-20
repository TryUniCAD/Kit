# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
import sqlite3
import subprocess
import sys

from InferenceGrid.CatalogueRunPlan import BuildRunPlan, RunOutcome
from InferenceGrid.CatalogueWorkerConfig import BuildWorkerCfg
from InferenceGrid.FeatureRoutes import FeatureRecipes
from InferenceGrid.Provision import CheckRevision
from Ledger import Ledger
from Pilot.PilotConfig import PilotConfig
from Pilot.PilotFiles import WriteRecord
from Records import bounded, read_record
from Supervisor import read_config

# the shared supervisor and ledger can admit at most this many workers
KMaxBatchWorkers = 64


# independent routes keep running when another route lacks local prerequisites
ScopeErrors = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    RuntimeError,
    sqlite3.Error,
    subprocess.SubprocessError,
)


# a private worker store keeps batch results separate from active research work
def RunCatalogueBatch(
    Directory,
    SourceRoot,
    Revision,
    Catalogues,
    MaxSeconds,
    Native,
    Advice=None,
    *,
    Reserve=None,
    Workers=KMaxBatchWorkers,
    NativeReady=False,
    FileScope=None,
    FileInput=None,
):
    Workers = bounded(Workers, 1, KMaxBatchWorkers)
    CheckRevision(Revision)
    if Directory.is_relative_to(SourceRoot):
        raise ValueError("use a new run directory outside the source checkout")
    Plan = BuildRunPlan(Catalogues, Revision)
    Directory.mkdir(mode=0o700)
    FileAdviceStatus = None
    if FileScope is not None:
        Audit, Reports = FileScope
        WriteRecord(Directory / "FileScope.json", Audit)
        for Layer, Report in Reports.items():
            WriteRecord(Directory / f"Input-{Layer}.json", Report)
            if Layer in ("reader-patch", "design-names", "state-repair", "timeline-names", "pattern-count-reader", "mirrored-field-reader"):
                Name = {"reader-patch": "Reader.patch", "mirrored-field-reader": "MirroredFields.patch", "pattern-count-reader": "SketchPatternCounts.patch", "design-names": "DesignNames.patch", "state-repair": "BrepTypes.patch", "timeline-names": "TimelineNames.patch"}[Layer]
                with (Directory / Name).open("x", encoding="utf-8") as Patch:
                    Patch.write(Report["patch"])
        from InferenceGrid.FileAdvice import advise_file, file_stall
        Stall = file_stall(Audit, Reports)
        if Stall is not None:
            WriteRecord(Directory / "FileStall.json", Stall)
            Selected = None
            if Advice is not None:
                FileAdviceStatus, Selected = advise_file(Directory, Stall, Advice)
                Advice = replace(Advice, calls=Advice.calls - 1) if Advice.calls > 1 else None
            Experiments = Stall["available_experiments"]
            if FileInput is not None and Experiments:
                from InferenceGrid.DepthControlReplay import replay_depth_edit
                Ordered = ([Selected] if Selected in Experiments else []) + [name for name in Experiments if name != Selected]
                Replays = [replay_depth_edit(SourceRoot, FileInput, Stall, name) for name in Ordered]
                WriteRecord(Directory / "FileExperiments.json", {"advisor_selection": Selected, "results": Replays})
    WriteRecord(Directory / "CataloguePlan.json", Plan)
    Store = Directory / "Store"
    Config, _, _ = PilotConfig(Directory, SourceRoot, Workers, GroupRescans=False)
    ClaimLimit = Workers if Native is None else KMaxBatchWorkers
    with Ledger(Store, create=True, max_running=ClaimLimit):
        pass
    if Native is not None:
        NativeConfig, _, _ = Native
        Controller = read_config(NativeConfig)["controller"]
        if Controller != {"adapter": "a03", "store": str(Store)}:
            raise ValueError("native supervisor must use this run's private A03 store")
    Submissions, Results = SubmitCatalogue(Directory, Plan, Store, Revision)
    PhaseJobs, Failures = {}, []
    if Submissions:
        PhaseJobs, Failures = RunPipeline(
            Directory,
            SourceRoot,
            Plan,
            Submissions,
            Config,
            Native,
            MaxSeconds,
            Advice,
            Reserve,
            NativeReady,
        )
    Results.update(ReadCatalogueJobs(Store, Submissions, PhaseJobs))
    Outcome = RunOutcome(Plan, Results, Failures)
    if FileScope is not None:
        if Stall is not None:
            if (Directory / "FileExperiments.json").exists():
                Outcome["file_experiments"] = str(Directory / "FileExperiments.json")
            Outcome["file_stall"] = str(Directory / "FileStall.json")
        if FileAdviceStatus is not None:
            Outcome["file_advice"] = {"status": FileAdviceStatus, "path": str(Directory / "FileAdvice/Advice.json")}
        Outcome["file_scope"] = str(Directory / "FileScope.json")
        if Outcome["status"] == "completed":
            Outcome["status"] = "coverage_incomplete"
    WriteRecord(Directory / "CatalogueResult.json", Outcome)
    return Outcome


# per scope submission receipts remain inspectable even before the batch finishes
def SubmitCatalogue(Directory, Plan, Store, Revision):
    Submissions, Results = {}, {}
    for Index, (Scope, Identity) in enumerate(Plan["scopes"].items(), 1):
        try:
            Receipt = FeatureRecipes[Identity].Submit(Store, Revision)
            if Receipt["scope"] != Scope:
                raise ValueError("submitted scope differs from the selected recipe")
            Submissions[Scope] = Receipt
        except ScopeErrors as Error:
            Results[Scope] = {
                "status": "failed",
                "stage": "submission",
                "reason": str(Error)[:2048],
            }
        WriteRecord(
            Directory / f"Submission{Index}.json",
            {
                "scope": Scope,
                "receipt": Submissions.get(Scope),
                "failure": Results.get(Scope),
            },
        )
        print(
            f"Prepared {Scope}: {'submitted' if Scope in Submissions else 'failed'}",
            file=sys.stderr,
            flush=True,
        )
    return Submissions, Results


# only submitted scopes with reviewed experiments may extend the native queue
def PlanHandoffs(Directory, Plan, Submissions, Native):
    if Native is None:
        return None
    _, KindName, Resource = Native
    Assessments = {
        Submissions[Scope]["assessment_job"]: Identity
        for Scope, Identity in Plan["scopes"].items()
        if Scope in Submissions and FeatureRecipes[Identity].Advance is not None
    }
    if not Assessments:
        return None
    return WriteRecord(
        Directory / "NativeHandoffs.json",
        {"kind": KindName, "resource": Resource, "assessments": Assessments},
    )


# one scheduler overlaps independent work while preserving accepted dependencies
def RunPipeline(
    Directory,
    SourceRoot,
    Plan,
    Submissions,
    Config,
    Native,
    MaxSeconds,
    Advice,
    Reserve,
    NativeReady,
):
    Failures, Phases = [], {}
    Handoffs = None
    Stage = "Offline"
    try:
        Handoffs = PlanHandoffs(Directory, Plan, Submissions, Native)
        if Handoffs is not None:
            NativePath, KindName, Resource = Native
            PipelineConfig = BuildWorkerCfg(
                Directory, Config, NativePath, KindName, Resource
            )
            if NativeReady:
                with Ledger(Directory / "Store") as State:
                    State.resource(Resource, available=True, capacity=1)
            Config = PipelineConfig
            Stage = "Pipeline"
    except ScopeErrors as Error:
        Handoffs = None
        Failures.append({"stage": "native_evidence", "reason": str(Error)[:2048]})
    Failure = RunSupervisor(
        Directory,
        SourceRoot,
        Config,
        MaxSeconds,
        Stage,
        Advice,
        Reserve=Reserve,
        Handoffs=Handoffs,
    )
    if Failure:
        Failures.append(Failure)
    if Handoffs is not None:
        HandoffResult = Directory / "NativeHandoffResult.json"
        if HandoffResult.is_file():
            Record = read_record(HandoffResult)
            Phases = Record["phases"]
            Failures.extend(Record["failures"])
        elif not Failure:
            Failures.append(
                {"stage": "native_evidence", "reason": "missing handoff result"}
            )
    return Phases, Failures


# the established supervisor executes each claim and retains its own durable receipts
def RunSupervisor(
    Directory,
    SourceRoot,
    Config,
    MaxSeconds,
    Stage,
    Advice=None,
    *,
    Reserve=None,
    Handoffs=None,
):
    AdviceArgs = Advice.arguments() if Advice else []
    MemoryArgs = [] if Reserve is None else ["--reserved-memory-mib", str(Reserve)]
    HandoffArgs = [] if Handoffs is None else ["--catalogue-handoffs", str(Handoffs)]
    AdviceSeconds = 90 * Advice.calls if Advice else 0
    try:
        with (Directory / f"{Stage}Supervisor.log").open("xb") as Log:
            Process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SourceRoot / "re/automation/Supervisor.py"),
                    "--config",
                    str(Config),
                    "run",
                    "--idle-seconds",
                    "8",
                    "--max-seconds",
                    str(MaxSeconds),
                    *AdviceArgs,
                    *MemoryArgs,
                    *HandoffArgs,
                ],
                cwd=SourceRoot,
                stdout=Log,
                stderr=subprocess.STDOUT,
                timeout=MaxSeconds + AdviceSeconds + 90,
                check=False,
            )
        if Process.returncode:
            return {"stage": Stage, "exit_code": Process.returncode}
    except (OSError, subprocess.TimeoutExpired) as Error:
        return {"stage": Stage, "reason": str(Error)[:2048]}
    return None


# controller receipts are the authority for the batch's completed and blocked work
def ReadCatalogueJobs(Store, Submissions, PhaseJobs):
    Results = {}
    with Ledger(Store) as State:
        for Scope, Receipt in Submissions.items():
            Identities = [Job["id"] for Job in Receipt["jobs"]]
            Identities.extend(PhaseJobs.get(Scope, {}).values())
            Jobs = [State.status(Identity)["jobs"][0] for Identity in Identities]
            States = {Job["state"] for Job in Jobs}
            if States == {"completed"}:
                Status = "completed"
            elif States & {"rejected", "failed"}:
                Status = "failed"
            else:
                Status = next(
                    (
                        Item
                        for Item in (
                            "running",
                            "queued",
                            "waiting_application",
                            "waiting_evidence",
                            "waiting_ci",
                        )
                        if Item in States
                    ),
                    "unfinished",
                )
            Results[Scope] = {
                "status": Status,
                "assessment_job": Receipt["assessment_job"],
                "jobs": Jobs,
            }
    return Results
