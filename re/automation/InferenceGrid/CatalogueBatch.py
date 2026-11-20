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

from InferenceGrid.CatalogueProgress import ObserveCatalogue
from InferenceGrid.CatalogueRunPlan import BuildRunPlan, RunOutcome
from InferenceGrid.CatalogueRuntime import (
    HoldCatalogue,
    ReadRun,
    ReadRunOptions,
    ReadSubmissions,
    SaveRun,
)
from InferenceGrid.CatalogueWorkerConfig import BuildWorkerCfg
from InferenceGrid.FeatureRoutes import FeatureRecipes
from InferenceGrid.Provision import CheckRevision
from Ledger import Ledger
from Pilot.PilotConfig import PilotConfig
from Pilot.PilotFiles import WriteRecord
from Records import bounded, read_record
from Sessions import write_private
from Supervisor import read_config

# the shared supervisor and ledger can admit at most this many workers
KMaxBatchWorkers = 64


# short groups reuse the sdk while leaving enough work for other workers
KCatalogueGroupSize = 4


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
    with HoldCatalogue(Directory):
        if FileScope is not None:
            Audit, Reports = FileScope
            WriteRecord(Directory / "FileScope.json", Audit)
            for Layer, Report in Reports.items():
                WriteRecord(Directory / f"Input-{Layer}.json", Report)
                if Layer in ("scalar-stream-reader", "reader-patch", "design-names", "state-repair", "timeline-names", "pattern-count-reader", "mirrored-field-reader"):
                    Name = {"scalar-stream-reader": "NamedScalarReader.patch", "reader-patch": "Reader.patch", "mirrored-field-reader": "MirroredFields.patch", "pattern-count-reader": "SketchPatternCounts.patch", "design-names": "DesignNames.patch", "state-repair": "BrepTypes.patch", "timeline-names": "TimelineNames.patch"}[Layer]
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
                    if Stall["focus"] == "counted_text_gap":
                        from InferenceGrid.CountedText import resume_text
                        Replays = [resume_text(FileInput, Stall["source_sha256"], Reports["raw-structure"]["counted_text"], name) for name in Ordered]
                    else:
                        Replays = [replay_depth_edit(SourceRoot, FileInput, Stall, name) for name in Ordered]
                    WriteRecord(Directory / "FileExperiments.json", {"advisor_selection": Selected, "results": Replays})
        WriteRecord(Directory / "CataloguePlan.json", Plan)
        Store = Directory / "Store"
        Config, _, _ = PilotConfig(
            Directory, SourceRoot, Workers, GroupMaxMembers=KCatalogueGroupSize
        )
        ClaimLimit = min(KMaxBatchWorkers, Workers * KCatalogueGroupSize)
        if Native is not None:
            ClaimLimit = KMaxBatchWorkers
        with Ledger(Store, create=True, max_running=ClaimLimit):
            pass
        if Native is not None:
            NativeConfig, _, _ = Native
            Controller = read_config(NativeConfig)["controller"]
            if Controller != {"adapter": "a03", "store": str(Store)}:
                raise ValueError(
                    "native supervisor must use this run's private A03 store"
                )
        Submissions, Results = SubmitCatalogue(Directory, Plan, Store, Revision)
        Stage, Failures = PreparePipeline(Directory, Plan, Submissions, Config, Native)
        Resource = Native[2] if Stage == "Pipeline" else None
        SaveRun(Directory, Plan, Stage, Failures, MaxSeconds, Reserve, Advice, Resource)
        return FinishCatalogue(
            Directory,
            SourceRoot,
            Plan,
            Stage,
            Failures,
            Submissions,
            Results,
            MaxSeconds,
            Advice,
            Reserve,
            Resource,
            NativeReady,
            Resume=False,
        )


# the controller retains successful receipts across stops and restarts
def ResumeCatalogue(Directory, SourceRoot, Format, MaxSeconds, NativeReady):
    with HoldCatalogue(Directory):
        Plan, Run = ReadRun(Directory, SourceRoot, Format)
        Submissions, Results = ReadSubmissions(Directory, Plan)
        Advice, Reserve, Seconds = ReadRunOptions(Run, MaxSeconds)
        if NativeReady and Run["stage"] != "Pipeline":
            raise ValueError("this saved run has no configured native worker")
        (Directory / "CataloguePause.json").unlink(missing_ok=True)
        return FinishCatalogue(
            Directory,
            SourceRoot,
            Plan,
            Run["stage"],
            Run["failures"],
            Submissions,
            Results,
            Seconds,
            Advice,
            Reserve,
            Run["native_resource"],
            NativeReady,
            Resume=True,
        )


# the latest report is replaceable while accepted receipts remain immutable
def FinishCatalogue(
    Directory,
    SourceRoot,
    Plan,
    Stage,
    Failures,
    Submissions,
    Results,
    MaxSeconds,
    Advice,
    Reserve,
    Resource,
    NativeReady,
    *,
    Resume,
):
    Failures = list(Failures)
    Store = Directory / "Store"
    Phases = {}
    if Stage is not None:
        Config = Directory / (
            "PipelineSupervisor.json" if Stage == "Pipeline" else "Supervisor.json"
        )
        Handoffs = Directory / "NativeHandoffs.json" if Stage == "Pipeline" else None
        if NativeReady and Resource is not None:
            with Ledger(Store) as State:
                State.resource(Resource, available=True, capacity=1)
        Failure = RunSupervisor(
            Directory,
            SourceRoot,
            Config,
            MaxSeconds,
            Stage,
            Advice,
            Reserve=Reserve,
            Handoffs=Handoffs,
            Resume=Resume,
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
    Results.update(ReadCatalogueJobs(Store, Submissions, Phases))
    Outcome = RunOutcome(Plan, Results, Failures)
    if (Directory / "FileScope.json").is_file():
        for Key, Name in (("file_scope", "FileScope.json"), ("file_stall", "FileStall.json"),
                          ("file_experiments", "FileExperiments.json"), ("reader_patch", "Reader.patch"),
                          ("scalar_reader_patch", "NamedScalarReader.patch")):
            if (Directory / Name).is_file():
                Outcome[Key] = str(Directory / Name)
        AdvicePath = Directory / "FileAdvice/Advice.json"
        if AdvicePath.is_file():
            Outcome["file_advice"] = {"status": read_record(AdvicePath)["status"], "path": str(AdvicePath)}
        if Outcome["status"] == "completed":
            Outcome["status"] = "coverage_incomplete"
    from NativeAcceptance.CatalogueBatch import VerifyCatalogue

    Verification = VerifyCatalogue(SourceRoot, Directory, Results)
    Outcome["native_verification"] = Verification
    if Verification and any(Item["status"] != "passed" for Item in Verification.values()):
        if Outcome["status"] == "completed":
            Outcome["status"] = "coverage_incomplete"
    if Outcome["status"] == "completed" and not Verification:
        Outcome["status"] = "coverage_incomplete"
    if (Directory / "CataloguePause.json").is_file() and Outcome[
        "status"
    ] == "coverage_incomplete":
        Outcome["status"] = "paused"
    write_private(Directory / "CatalogueResult.json", Outcome)
    return Outcome


# per scope submission receipts remain inspectable even before the batch finishes
def SubmitCatalogue(Directory, Plan, Store, Revision):
    Submissions, Results = {}, {}
    Dependencies = []
    Blocked = None
    for Index, Scope in enumerate(Plan["scope_order"], 1):
        Identity = Plan["scopes"][Scope]
        try:
            if Blocked is not None:
                raise ValueError(f"preceding scope could not be submitted: {Blocked}")
            Receipt = FeatureRecipes[Identity].Submit(Store, Revision, Dependencies=Dependencies)
            if Receipt["scope"] != Scope:
                raise ValueError("submitted scope differs from the selected recipe")
            Submissions[Scope] = Receipt
            Dependencies = [Job["id"] for Job in Receipt["jobs"]]
        except ScopeErrors as Error:
            Blocked = Scope
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


# the prepared pipeline is reused without changing its reviewed routing on restart
def PreparePipeline(Directory, Plan, Submissions, Config, Native):
    if not Submissions:
        return None, []
    try:
        Handoffs = PlanHandoffs(Directory, Plan, Submissions, Native)
        if Handoffs is not None:
            NativePath, KindName, Resource = Native
            BuildWorkerCfg(Directory, Config, NativePath, KindName, Resource)
            return "Pipeline", []
    except ScopeErrors as Error:
        return "Offline", [{"stage": "native_evidence", "reason": str(Error)[:2048]}]
    return "Offline", []


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
    Resume=False,
):
    AdviceArgs = Advice.arguments() if Advice else []
    MemoryArgs = [] if Reserve is None else ["--reserved-memory-mib", str(Reserve)]
    HandoffArgs = [] if Handoffs is None else ["--catalogue-handoffs", str(Handoffs)]
    AdviceSeconds = 90 * Advice.calls if Advice else 0
    PauseArgs = ["--catalogue-pause-file", str(Directory / "CataloguePause.json")]
    try:
        LogPath = Directory / f"{Stage}Supervisor.log"
        with LogPath.open("ab" if Resume else "xb") as Log:
            with ObserveCatalogue(Directory, LogPath, Log.tell()):
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
                        *PauseArgs,
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
