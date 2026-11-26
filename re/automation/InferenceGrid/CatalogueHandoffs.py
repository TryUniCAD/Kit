# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from concurrent.futures import ThreadPoolExecutor
import sqlite3
import subprocess

from InferenceGrid.FeatureRoutes import FeatureRecipes
from Sessions import write_private
from Records import label, read_record


# handoff inputs contain only reviewed routes and their submitted assessment identities
def ReadHandoffs(Manifest, ConfigPath, Store):
    Record = read_record(Manifest)
    if not isinstance(Record, dict) or set(Record) != {
        "kind",
        "resource",
        "assessments",
    }:
        raise ValueError("invalid catalogue handoff plan")
    KindName = label(Record["kind"])
    Resource = label(Record["resource"])
    Assessments = Record["assessments"]
    if not isinstance(Assessments, dict) or not 1 <= len(Assessments) <= 64:
        raise ValueError(
            "catalogue handoff plan requires one to sixty four assessments"
        )
    Routes, Attached, Parked = {}, {}, []
    for JobName, Identity in Assessments.items():
        Recipe = FeatureRecipes.get(label(Identity))
        if Recipe is None or Recipe.Advance is None:
            raise ValueError("handoff requires a reviewed native route")
        Status = Recipe.Status(Store)
        if Status["assessment"]["id"] != label(JobName):
            raise ValueError("handoff route does not own the submitted assessment")
        if any(Item.Scope == Recipe.Scope for Item in Routes.values()):
            raise ValueError("duplicate catalogue handoff scope")
        Routes[JobName] = Recipe
        if Status["status"] == "experiment_attached":
            Attached[Recipe.Scope] = Status["phase_jobs"]
        elif Status["status"] == "experiment_needed":
            Parked.append(JobName)
    Routes = {
        JobName: Route
        for JobName, Route in Routes.items()
        if Route.Scope not in Attached
    }
    return CatalogueHandoffs(
        Manifest, ConfigPath, Store, KindName, Resource, Routes, Attached, Parked
    )


# verified native preparation runs beside decoding instead of blocking the supervisor loop
class CatalogueHandoffs:
    def __init__(
        self, Manifest, ConfigPath, Store, KindName, Resource, Routes, Attached, Parked
    ):
        self.Output = Manifest.with_name("NativeHandoffResult.json")
        self.ConfigPath = ConfigPath
        self.Store = Store
        self.KindName = KindName
        self.Resource = Resource
        self.Routes = Routes
        self.Pending = {}
        self.Phases = Attached
        self.Parked = Parked
        self.Failures = []
        self.Executor = ThreadPoolExecutor(max_workers=1)

    def Start(self):
        for JobName in self.Parked:
            self.Notify(JobName)

    def Notify(self, JobName):
        Recipe = self.Routes.pop(JobName, None)
        if Recipe is not None:
            self.Pending[Recipe.Scope] = self.Executor.submit(
                Recipe.Advance,
                self.Store,
                self.ConfigPath,
                self.KindName,
                self.Resource,
                0,
            )

    def Poll(self, Report):
        Active = bool(self.Pending)
        for Scope, Future in list(self.Pending.items()):
            if not Future.done():
                continue
            del self.Pending[Scope]
            if Future.cancelled():
                continue
            try:
                Result = Future.result()
                if Result["status"] != "experiment_attached":
                    raise ValueError(
                        "settled assessment did not attach its native experiment"
                    )
                self.Phases[Scope] = Result["phase_jobs"]
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                RuntimeError,
                sqlite3.Error,
                subprocess.SubprocessError,
            ) as Error:
                Failure = {
                    "stage": "native_evidence",
                    "scope": Scope,
                    "reason": str(Error)[:2048],
                }
                self.Failures.append(Failure)
                Report("catalogue_handoff_failed", None, Failure)
            else:
                Report(
                    "catalogue_handoff",
                    None,
                    {"scope": Scope, "jobs": self.Phases[Scope]},
                )
        return Active

    def Close(self, Report):
        self.Executor.shutdown(cancel_futures=True)
        self.Poll(Report)
        write_private(self.Output, {"phases": self.Phases, "failures": self.Failures})
