# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from time import time
from contextlib import contextmanager
from os import close
from Supervisor import lock

from InferenceGrid.BuilderDevelopment.Queue import DriveStage, SubmitStage, ReadStage
from InferenceGrid.RecipeCampaign.CampaignState import WriteState
from Records import digest


# locking before preparation prevents competing resumes from changing the same journal or budgets
@contextmanager
def HoldBuilderRun(Directory):
    Directory.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    Descriptor = lock(Directory.parent / (Directory.name + ".Builder.lock"))
    try:
        yield
    finally:
        close(Descriptor)


# interruption and exhausted budgets retain a durable resumable job instead of losing its attempts
class DevelopmentStopped(Exception):
    def __init__(self, Classification, Detail=None):
        self.classification = Classification
        self.detail = Detail
        super().__init__(Classification)


# all stage submissions are persisted before dispatch and recover through existing controller receipts
class StageState:
    def __init__(self, Directory, SourceRoot, Job, State, ConfigPath):
        self.directory, self.source_root = Directory, SourceRoot
        self.job, self.state, self.config = Job, State, ConfigPath

    def Save(self):
        WriteState(self.directory / "BuilderState.json", self.state)

    def Check(self):
        from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
            VerifierPins,
        )

        if VerifierPins() != self.job["independent_verifier_sources"]:
            raise DevelopmentStopped("frozen_verifier_changed")
        if (self.directory / "CataloguePause.json").exists():
            raise DevelopmentStopped("paused")
        if time() >= self.state["deadline"]:
            raise DevelopmentStopped("time_budget_exhausted")

    def Stage(self, Key, Kind, Inputs, Dependencies=None, Native=False):
        self.Check()
        Key += ":" + digest([Inputs, Dependencies or {}])[:16]
        BaseKey = Key
        Heads = self.state.setdefault("stage_heads", {})
        Key = Heads.get(BaseKey, BaseKey)
        Epoch = self.state.get("recovery_epoch", 0)
        if Key in self.state["jobs"] and Epoch:
            Previous = ReadStage(self.directory, self.state["jobs"][Key])
            if Previous["status"] in {"failed", "rejected"} or (
                Native
                and (
                    Previous.get("records", {}).get("status") == "blocked"
                    or self.state["jobs"][Key]
                    in self.state.get("retry_native_jobs", [])
                )
            ):
                Inputs = {**Inputs, "execution_retry": Epoch}
                Key = BaseKey + ".retry" + str(Epoch)
        if Key not in self.state["jobs"]:
            self.state["jobs"][Key] = SubmitStage(
                self.directory,
                self.job,
                Kind,
                {"job": self.job, **Inputs},
                Dependencies,
                "application:solidworks:catalogue" if Native else None,
            )
            Heads[BaseKey] = Key
            self.Save()
        Identity = self.state["jobs"][Key]
        Result = DriveStage(
            self.directory,
            self.source_root,
            self.config,
            Identity,
            self.state["deadline"] - time(),
        )
        if (self.directory / "CataloguePause.json").exists():
            raise DevelopmentStopped("paused", Result)
        if Result["status"] != "completed":
            raise DevelopmentStopped("execution_incomplete", Result)
        return Identity, Result["records"], Result
