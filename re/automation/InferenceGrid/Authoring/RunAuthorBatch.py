# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from contextlib import nullcontext

from InferenceGrid.Authoring.AuthorConfig import AuthorConfig
from InferenceGrid.Authoring.AuthorOutcome import AuthorOutcome
from InferenceGrid.Authoring.BuildAuthorPlan import BuildAuthorPlan
from InferenceGrid.Authoring.SubmitFusion import SubmitFusion
from InferenceGrid.Authoring.SubmitSolid import SubmitSolid
from InferenceGrid.CatalogueBatch import RunSupervisor
from InferenceGrid.CatalogueRuntime import HoldCatalogue
from InferenceGrid.Provision import CheckRevision
from Ledger import Ledger
from Pilot.PilotFiles import WriteRecord
from Records import digest, read_record
from Sessions import write_private


# prepared authoring jobs survive pauses without changing their native sample identities
def RunAuthorBatch(
    Directory,
    SourceRoot,
    Revision,
    Catalogues,
    MaxSeconds,
    Native,
    *,
    CasePath=None,
    ModeValue="discovery",
    HostPath=None,
    Reserve=None,
    Workers=4,
    NativeReady=False,
    PrepareOnly=False,
    LifecyclePath=None,
):
    Directory = Path(Directory).resolve()
    if Directory.is_relative_to(SourceRoot):
        raise ValueError("use an authoring run directory outside the source checkout")
    PlanValue = BuildAuthorPlan(Catalogues, Revision, CasePath, ModeValue)
    Applications = {Value["application"] for Value in PlanValue["samples"].values()}
    if not PrepareOnly and (
        ("fusion" in Applications and Native is None)
        or ("solidworks" in Applications and HostPath is None)
    ):
        raise ValueError(
            "selected authoring cases require their configured native host"
        )
    if not PrepareOnly and "fusion" in Applications and LifecyclePath is None:
        raise ValueError(
            "Fusion authoring requires --fusion-lifecycle for automatic fresh process verification"
        )
    if not PrepareOnly:
        CheckRevision(Revision)
    Directory.mkdir(mode=0o700)
    with HoldCatalogue(Directory):
        WriteRecord(Directory / "AuthoringPlan.json", PlanValue)
        if PrepareOnly:
            ResultValue = {
                "schema_version": 1,
                "status": "prepared",
                "plan": str(Directory / "AuthoringPlan.json"),
                "samples": len(PlanValue["samples"]),
                "features": PlanValue["features"],
            }
            write_private(Directory / "CatalogueResult.json", ResultValue)
            return ResultValue
        with Ledger(Directory / "Store", create=True, max_running=64):
            pass
        ConfigPath, Resources = AuthorConfig(
            Directory, SourceRoot, Workers, Native, HostPath
        )
        FusionConfig = (
            None
            if Native is None
            else [str(Directory / "NativeSupervisor.json"), Native[1], Native[2]]
        )
        ConfigValue = read_record(ConfigPath)
        RuntimePins = {
            str(ConfigPath): digest(ConfigValue),
            ConfigValue["registry"]: digest(read_record(Path(ConfigValue["registry"]))),
        }
        if HostPath is not None:
            RuntimePins[str(Directory / "SolidWorksHost.json")] = digest(
                read_record(Directory / "SolidWorksHost.json")
            )
        LifecycleFile = None
        InstallationFile = None
        if "fusion" in Applications:
            LifecycleFile = WriteRecord(
                Directory / "FusionLifecycle.json", read_record(LifecyclePath)
            )
            RegistryValue = read_record(Path(ConfigValue["registry"]))
            RunnerValue = RegistryValue["runners"][Native[1]]
            InstallationFile = str((SourceRoot / RunnerValue["argv"][-2]).resolve())
            RuntimePins[str(LifecycleFile)] = digest(read_record(LifecycleFile))
            RuntimePins[InstallationFile] = digest(read_record(Path(InstallationFile)))
        RunValue = {
            "version": 1,
            "plan_sha256": digest(PlanValue),
            "config": str(ConfigPath),
            "runtime_pins": RuntimePins,
            "resources": Resources,
            "native": FusionConfig,
            "lifecycle": None if LifecycleFile is None else str(LifecycleFile),
            "installation": InstallationFile,
            "max_seconds": MaxSeconds,
            "reserve": Reserve,
        }
        WriteRecord(Directory / "AuthoringRun.json", RunValue)
        return FinishAuthor(
            Directory,
            SourceRoot,
            PlanValue,
            RunValue,
            MaxSeconds,
            NativeReady,
            Resume=False,
        )


# every resume uses the exact original plan source revision and host configuration
def ResumeAuthor(Directory, SourceRoot, FormatValue, MaxSeconds, NativeReady):
    with HoldCatalogue(Directory):
        PlanValue, RunValue = ReadAuthorRun(Directory, SourceRoot, FormatValue)
        (Directory / "CataloguePause.json").unlink(missing_ok=True)
        return FinishAuthor(
            Directory,
            SourceRoot,
            PlanValue,
            RunValue,
            RunValue["max_seconds"] if MaxSeconds is None else MaxSeconds,
            NativeReady,
            Resume=True,
        )


# authoring preparation never replaces a queued native phase or an accepted decoder receipt
def FinishAuthor(
    Directory, SourceRoot, PlanValue, RunValue, MaxSeconds, NativeReady, *, Resume
):
    Submissions = []
    if "solidworks" in RunValue["resources"]:
        Submissions.extend(
            SubmitSolid(Directory, PlanValue, RunValue["resources"]["solidworks"])
        )
    if RunValue["native"] is not None:
        Native = RunValue["native"]
        Submissions.extend(
            SubmitFusion(Directory, PlanValue, (Path(Native[0]), Native[1], Native[2]))
        )
    write_private(Directory / "AuthoringSubmissions.json", {"submissions": Submissions})
    if NativeReady:
        with Ledger(Directory / "Store") as StateValue:
            for Resource in RunValue["resources"].values():
                StateValue.resource(Resource, available=True, capacity=1)
    Lifecycle = nullcontext()
    if RunValue["lifecycle"] is not None:
        from InferenceGrid.Authoring.FusionLifecycle import OwnFusionLife

        Lifecycle = OwnFusionLife(
            Directory,
            SourceRoot,
            Path(RunValue["config"]),
            Path(RunValue["installation"]),
            Path(RunValue["lifecycle"]),
            Resume=Resume,
        )
    with Lifecycle as GuardValue:
        FailureValue = RunSupervisor(
            Directory,
            SourceRoot,
            Path(RunValue["config"]),
            MaxSeconds,
            "Authoring",
            Reserve=RunValue["reserve"],
            Resume=Resume,
            CheckRunning=None if GuardValue is None else GuardValue.CheckAlive,
        )
    ResultValue = AuthorOutcome(
        Directory,
        PlanValue,
        Submissions,
        [] if FailureValue is None else [FailureValue],
    )
    if (Directory / "CataloguePause.json").is_file() and ResultValue[
        "status"
    ] == "coverage_incomplete":
        ResultValue["status"] = "paused"
    write_private(Directory / "CatalogueResult.json", ResultValue)
    return ResultValue


# saved host settings cannot be reused for a different source or selected catalogue
def ReadAuthorRun(Directory, SourceRoot, FormatValue=None):
    Directory = Path(Directory).resolve()
    if Directory.is_relative_to(SourceRoot):
        raise ValueError("authoring run must be outside the source checkout")
    PlanValue = read_record(Directory / "AuthoringPlan.json")
    RunValue = read_record(Directory / "AuthoringRun.json")
    if RunValue.get("version") != 1 or RunValue.get("plan_sha256") != digest(PlanValue):
        raise ValueError("saved authoring run differs from its prepared plan")
    if FormatValue is not None and set(PlanValue["catalogues"]) != {FormatValue}:
        raise ValueError("saved authoring run uses another catalogue format")
    if any(
        digest(read_record(Path(FileName))) != PinValue
        for FileName, PinValue in RunValue["runtime_pins"].items()
    ):
        raise ValueError("saved authoring worker configuration changed")
    CheckRevision(PlanValue["source_revision"])
    return PlanValue, RunValue
