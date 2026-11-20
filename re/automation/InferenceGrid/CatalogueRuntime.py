# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import contextmanager
from dataclasses import asdict
from os import close

from CodexAdvice.AdviceOptions import AdviceOptions
from InferenceGrid.Provision import CheckRevision
from Pilot.PilotFiles import WriteRecord
from Records import bounded, digest, read_record
from Sessions import write_private
from Supervisor import bound_memory_reserve, lock


# only one catalogue process may dispatch or update the same run
@contextmanager
def HoldCatalogue(Directory):
    Descriptor = lock(Directory / "Catalogue.lock")
    try:
        yield
    finally:
        close(Descriptor)


# persistence excludes provider credentials and binds the prepared run to its exact inputs
def SaveRun(Directory, Plan, Stage, Failures, MaxSeconds, Reserve, Advice, Resource):
    return WriteRecord(
        Directory / "CatalogueRun.json",
        {
            "version": 1,
            "plan_sha256": digest(Plan),
            "stage": Stage,
            "failures": Failures,
            "max_seconds": MaxSeconds,
            "reserve": Reserve,
            "advice": None if Advice is None else asdict(Advice),
            "native_resource": Resource,
        },
    )


# continuing a different revision could produce evidence under the wrong source identity
def ReadRun(Directory, SourceRoot, Format):
    if Directory.is_relative_to(SourceRoot):
        raise ValueError("use a run directory outside the source checkout")
    Plan = read_record(Directory / "CataloguePlan.json")
    Run = read_record(Directory / "CatalogueRun.json")
    if Run.get("version") != 1 or Run.get("plan_sha256") != digest(Plan):
        raise ValueError("saved catalogue run does not match its prepared plan")
    if Format is not None and set(Plan["catalogues"]) != {Format}:
        raise ValueError("saved catalogue run uses a different format")
    CheckRevision(Plan["source_revision"])
    if Run["stage"] not in (None, "Offline", "Pipeline"):
        raise ValueError("invalid saved catalogue stage")
    return Plan, Run


# accepted submissions are reused directly rather than submitted a second time
def ReadSubmissions(Directory, Plan):
    Submissions, Results = {}, {}
    for Index, Scope in enumerate(Plan["scopes"], 1):
        Entry = read_record(Directory / f"Submission{Index}.json")
        if Entry["scope"] != Scope or (Entry["receipt"] is None) == (
            Entry["failure"] is None
        ):
            raise ValueError("saved catalogue submission does not match its scope")
        if Entry["receipt"] is not None:
            if Entry["receipt"]["scope"] != Scope:
                raise ValueError("saved receipt does not match its scope")
            Submissions[Scope] = Entry["receipt"]
        else:
            Results[Scope] = Entry["failure"]
    return Submissions, Results


# launch options remain scoped to the private saved catalogue run
def ReadRunOptions(Run, MaxSeconds):
    Advice = None if Run["advice"] is None else AdviceOptions(**Run["advice"])
    Reserve = None if Run["reserve"] is None else bound_memory_reserve(Run["reserve"])
    Seconds = bounded(
        Run["max_seconds"] if MaxSeconds is None else MaxSeconds, 1, 86400
    )
    return Advice, Reserve, Seconds


# pause is a durable request to stop claiming new work without interrupting active workers
def PauseCatalogue(Directory, SourceRoot, Format):
    _, Run = ReadRun(Directory, SourceRoot, Format)
    if Run["stage"] is not None:
        write_private(Directory / "CataloguePause.json", {"paused": True})
    return {
        "status": "pausing" if Run["stage"] is not None else "no_workers",
        "directory": str(Directory),
    }
