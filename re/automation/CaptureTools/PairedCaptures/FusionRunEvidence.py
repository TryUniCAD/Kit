# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import file_digest, sha256
from json import loads
from math import isfinite
from re import fullmatch

from Corpus import git
from OutputFiles import open_output
from PairedCaptures.FusionFreshProcess import BINDINGS, CONTROL, HELPER, RECIPES, SCHEMA, SPEC, TOOL
from PairedCaptures.FusionRunReadbacks import CheckControl, CheckRecipeRead


# manual receipts use the same size bound as the committed corpus intake
JsonReadLimit = 32 * 1024 * 1024


# ambiguous record keys would allow different readers to interpret different evidence
def DecodePairs(Pairs):
    Result = dict(Pairs)
    if len(Result) != len(Pairs):
        raise ValueError("Fusion evidence JSON contains a duplicate key")
    return Result


# observation metadata must have a portable representation in the receipt
def RejectNumber(Number):
    raise ValueError(f"invalid Fusion evidence JSON number {Number}")


# the run reports can be large but must be read without following evidence links
def ReadRecord(RunFolder, Name):
    with open_output(RunFolder, Name) as Source:
        DataBytes = Source.read(JsonReadLimit + 1)
    if len(DataBytes) > JsonReadLimit:
        raise ValueError(f"Fusion evidence JSON exceeds the intake limit: {Name}")
    Payload = loads(DataBytes, object_pairs_hook=DecodePairs, parse_constant=RejectNumber)
    if not isinstance(Payload, dict):
        raise ValueError(f"Fusion evidence JSON is not an object: {Name}")
    return Payload, sha256(DataBytes).hexdigest()


# historical plans must name the same complete archive roster already audited by intake
def MatchHistory(History, Capture, ReadPin):
    Receipt = ReadPin(Capture["receipt"]["path"])
    Measures = ReadPin(Capture["measurements"]["path"])
    Archives = {}
    Variants = {}
    for Entry in Capture["native_files"]:
        Native = {Name: Entry[Name] for Name in ("path", "sha256", "size_bytes")}
        if ReadPin(Native["path"]) != Native:
            raise ValueError(f"Fusion historical archive changed across revisions: {Native['path']}")
        Variant = Entry["variant"]
        if Variant in ("baseline-a", "baseline-b"):
            Archives[Variant[-1]] = Native
        else:
            Variants[Native["path"].rsplit("/", 1)[1]] = Native
    if (
        Receipt["sha256"] != Capture["receipt"]["sha256"]
        or Measures["sha256"] != Capture["measurements"]["sha256"]
        or History != {"receipt": Receipt, "measurements": Measures, "archives": Archives, "variants": Variants}
    ):
        raise ValueError(f"Fusion historical pins do not match the audited capture: {Capture['recipe_id']}")


# a local run may predate intake but its committed authoring inputs must remain traceable
def CheckPlan(Snapshot, Revision, PlanData, CaptureRows, SpecsDigest):
    RecipeIds = PlanData["recipes"]
    RunRevision = PlanData["source_revision"]
    if (
        PlanData["schema"] != SCHEMA
        or not isinstance(RunRevision, str)
        or not fullmatch(r"[0-9a-f]{40}", RunRevision)
        or not isinstance(RecipeIds, list)
        or not RecipeIds
        or len(RecipeIds) != len(set(RecipeIds))
        or not set(RecipeIds) <= set(RECIPES)
        or set(PlanData["existing"]) != set(RecipeIds)
    ):
        raise ValueError("Fusion evidence requires an exact non-holdout recipe and historical roster")
    git(Snapshot.root, "merge-base", "--is-ancestor", RunRevision, Revision)

    # the fixed input paths must never be chosen by the external receipt
    def ReadPin(Name):
        Contents = Snapshot.blob(RunRevision, Name)
        return {"path": Name, "sha256": sha256(Contents).hexdigest(), "size_bytes": len(Contents)}

    Paths = {"tool": TOOL, "helper": HELPER, "bindings": BINDINGS, "specification": SPEC, "control": CONTROL}
    if (
        PlanData["pins"] != {Name: ReadPin(Location.as_posix()) for Name, Location in Paths.items()}
        or PlanData["pins"]["specification"]["sha256"] != SpecsDigest
    ):
        raise ValueError("Fusion plan inputs differ from the pinned Git source or intake specification")
    Selected = {
        Row["recipe_id"]: Row
        for Row in CaptureRows
        if Row["application"] == "fusion" and Row["recipe_id"] in RecipeIds
    }
    for Recipe in RecipeIds:
        MatchHistory(PlanData["existing"][Recipe], Selected[Recipe], ReadPin)
    return Selected


# each phase must agree with the independently anchored report and the sealed authored recipe
def CheckPhase(RunFolder, Phase, PlanData, PlanDigest, RecipeDigests, Report, Digest):
    Prefix = f"phase-{Phase}"
    Receipt = ReadRecord(RunFolder, f"{Prefix}/receipt.json")[0]
    Expected = {
        "schema": SCHEMA,
        "phase": Phase,
        "status": "complete",
        "plan_sha256": PlanDigest,
    }
    if (
        Receipt != {**Expected, "measurements_sha256": Digest}
        or any(Report[Name] != Value for Name, Value in Expected.items())
        or Report["source_revision"] != PlanData["source_revision"]
        or Report["pins"] != PlanData["pins"]
        or Report["errors"] != []
        or Report["authoring_recipe_sha256"] != RecipeDigests
        or Report["captures"].keys() != RecipeDigests.keys()
    ):
        raise ValueError(f"Fusion Phase {Phase.upper()} receipt, report or recipe pin does not match")
    CheckControl(Report, PlanData["pins"]["control"])
    for Recipe, Capture in Report["captures"].items():
        PinValue = Capture[f"save_{Phase}"]
        FileName = f"{Recipe}-fusion-fresh-baseline-{Phase}.f3d"
        if (
            PinValue["file"] != FileName
            or type(PinValue["size_bytes"]) is not int
            or PinValue["size_bytes"] <= 0
        ):
            raise ValueError(f"Fusion Phase {Phase.upper()} has an invalid archive pin: {Recipe}")
        with open_output(RunFolder, f"{Prefix}/{FileName}") as Source:
            Source.seek(0, 2)
            if Source.tell() != PinValue["size_bytes"]:
                raise ValueError(f"Fusion archive size changed: {FileName}")
            Source.seek(0)
            if file_digest(Source, "sha256").hexdigest() != PinValue["sha256"]:
                raise ValueError(f"Fusion archive digest changed: {FileName}")


# a repeat save is evidence of a restart only when the recorded processes differ
def CheckRestart(First, Repeat, FirstDigest):
    for Report in (First, Repeat):
        Process = Report["process"]
        if (
            type(Process["pid"]) is not int
            or Process["pid"] <= 0
            or type(Process["start_unix_seconds"]) is not int
            or Process["start_unix_seconds"] <= 0
            or type(Report["started_unix_seconds"]) is not float
            or type(Report["ended_unix_seconds"]) is not float
            or not isfinite(Report["started_unix_seconds"])
            or not isfinite(Report["ended_unix_seconds"])
            or not Process["start_unix_seconds"] <= Report["started_unix_seconds"] <= Report["ended_unix_seconds"]
        ):
            raise ValueError("Fusion recorded process identity or timestamps are invalid")
    if (
        First["previous_measurements_sha256"] is not None
        or Repeat["previous_measurements_sha256"] != FirstDigest
        or First["process"]["pid"] == Repeat["process"]["pid"]
        or Repeat["process"]["start_unix_seconds"] <= First["process"]["start_unix_seconds"]
        or Repeat["process"]["start_unix_seconds"] < int(First["ended_unix_seconds"])
        or not isinstance(First["fusion_version"], str)
        or not First["fusion_version"]
        or First["fusion_version"] != Repeat["fusion_version"]
    ):
        raise ValueError("Fusion Phase B does not record the pinned Phase A restart and build")


# supplemental observations do not alter the qualification gate or the original corpus
def VerifyFusionRun(Snapshot, Intake, RunFolder, TrustedDigest):
    if not fullmatch(r"[0-9a-f]{64}", TrustedDigest):
        raise ValueError("Fusion Phase B measurements SHA-256 must be lowercase hexadecimal")
    Repeat, RepeatDigest = ReadRecord(RunFolder, "phase-b/measurements.json")
    if RepeatDigest != TrustedDigest:
        raise ValueError("Fusion Phase B measurements do not match the independently recorded SHA-256")
    PlanData, PlanDigest = ReadRecord(RunFolder, "plan.json")
    First, FirstDigest = ReadRecord(RunFolder, "phase-a/measurements.json")
    if Repeat["plan_sha256"] != PlanDigest or Repeat["previous_measurements_sha256"] != FirstDigest:
        raise ValueError("Fusion Phase B does not pin the supplied plan and Phase A measurements")
    Selected = CheckPlan(
        Snapshot, Intake["source_revision"], PlanData, Intake["captures"], Intake["specifications_sha256"]
    )
    RecipeDigests = {Name: Row["canonical_recipe_sha256"] for Name, Row in Selected.items()}
    CheckPhase(RunFolder, "a", PlanData, PlanDigest, RecipeDigests, First, FirstDigest)
    CheckPhase(RunFolder, "b", PlanData, PlanDigest, RecipeDigests, Repeat, RepeatDigest)
    CheckRestart(First, Repeat, FirstDigest)
    Findings = {}
    for Recipe, Capture in Selected.items():
        Findings[Recipe] = {
            "split": Capture["split"],
            "permitted_use": Capture["permitted_use"],
            **CheckRecipeRead(
                Recipe, First["captures"][Recipe], Repeat["captures"][Recipe], PlanData["existing"][Recipe]
            ),
        }
    return {
        "capture_source_revision": PlanData["source_revision"],
        "fusion_version": First["fusion_version"],
        "plan_sha256": PlanDigest,
        "phase_a_measurements_sha256": FirstDigest,
        "phase_b_measurements_sha256": RepeatDigest,
        "phase_a_process": First["process"],
        "phase_b_process": Repeat["process"],
        "aggregate_loader_warnings": "unobservable",
        "control_readbacks": 4,
        "recipes": Findings,
    }
