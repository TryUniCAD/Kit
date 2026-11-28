# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads
from pathlib import Path
from subprocess import run
from sys import executable

from InferenceGrid.RecipeCampaign.CampaignState import WriteState


# existing authoring owns native processes controls artifact checks and dependent decoder jobs
def BuildCommand(Args, Entry, SourceRoot, AttemptPath, CasesPath):
    Application = Entry["application"]
    Catalogue = getattr(Args, Application + "_catalogue")
    Command = [
        executable,
        str(SourceRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
        "--directory",
        str(AttemptPath),
        "--" + Application + "-catalogue",
        str(Catalogue),
        "--author-samples",
        "--authoring-cases",
        str(CasesPath),
        "--capture-mode",
        Entry["mode"],
        "--authoring-grid",
        Args.authoring_grid,
        "--max-seconds",
        str(Args.recipe_seconds),
    ]
    Options = (
        ("solidworks_host",)
        if Application == "solidworks"
        else ("native_config", "native_kind", "native_resource", "fusion_lifecycle")
    )
    for Option in Options:
        Value = getattr(Args, Option)
        if Value is None:
            raise ValueError("missing --" + Option.replace("_", "-"))
        Command.extend(["--" + Option.replace("_", "-"), str(Value)])
    if Args.native_ready:
        Command.append("--native-ready")
    return Command


# per recipe attempts preserve failed evidence while assistant corrections use a fresh source revision
def ApplyRecipe(Args, Entry, SourceRoot, State):
    EntryPath = Args.directory / "Recipes" / Entry["key"]
    EntryPath.mkdir(parents=True, exist_ok=True)
    CasesPath = EntryPath / "Cases.json"
    WriteState(
        CasesPath,
        {
            "schema_version": 1,
            "cases": [
                {"application": Entry["application"], "feature": Alias}
                for Alias in Entry["aliases"]
            ],
        },
    )
    IsResume = Entry["status"] == "running" and bool(Entry["attempts"])
    AttemptPath = (
        Path(Entry["attempts"][-1]["directory"])
        if IsResume
        else EntryPath / ("Attempt" + str(len(Entry["attempts"]) + 1))
    )
    try:
        Command = BuildCommand(Args, Entry, SourceRoot, AttemptPath, CasesPath)
        if IsResume:
            Command = [
                executable,
                str(SourceRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
                "--directory",
                str(AttemptPath),
                "--resume",
                "--max-seconds",
                str(Args.recipe_seconds),
            ]
            if Args.native_ready:
                Command.append("--native-ready")
    except ValueError as Error:
        Entry.update(status="needs_host", assistant_error=str(Error))
        return
    Entry["status"] = "running"
    if not IsResume:
        Entry["attempts"].append({"directory": str(AttemptPath), "state": "running"})
    WriteState(Args.directory / "Campaign.json", State)
    WriteState(
        Args.directory / "ActiveRecipe.json", {"key": Entry["key"], "command": Command}
    )
    with (EntryPath / (AttemptPath.name + ".log")).open("ab") as Output:
        Result = run(Command, cwd=SourceRoot, stdout=Output, stderr=Output, check=False)
    ResultPath = AttemptPath / "CatalogueResult.json"
    Outcome = (
        loads(ResultPath.read_text(encoding="utf-8")) if ResultPath.exists() else {}
    )
    Samples = Outcome.get("samples", {})
    Verified = bool(Samples) and all(
        Sample.get("native_verified") is True for Sample in Samples.values()
    )
    DecoderDone = bool(Samples) and all(
        any(
            Job.get("kind") == "catalogue.decode" and Job.get("state") == "completed"
            for Job in Sample.get("jobs", [])
        )
        for Sample in Samples.values()
    )
    Entry["attempts"][-1].update(
        {
            "directory": str(AttemptPath),
            "exit_code": Result.returncode,
            "result": str(ResultPath),
            "native_verified": Verified,
            "decoder_completed": DecoderDone,
            "state": "finished",
        }
    )
    Entry["native_verified"] = Verified
    Entry["status"] = (
        "verified_decode_incomplete" if Verified and DecoderDone else "needs_assistant"
    )
    if (
        Verified
        and DecoderDone
        and all(Sample.get("status") == "read" for Sample in Samples.values())
    ):
        Entry["status"] = "verified_reader_report"
    if Entry["status"] == "needs_assistant":
        Entry["assistant_error"] = (
            "native or decoder execution did not complete; inspect the retained attempt log and receipts"
        )
    (Args.directory / "ActiveRecipe.json").unlink(missing_ok=True)
