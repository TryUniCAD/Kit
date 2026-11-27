# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import PIPE as PipeStream, Popen as StartProcess
from time import monotonic as MonoTime, sleep as WaitBriefly
from types import TracebackType
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)


# real controller processes retain independent ownership while concurrent workers share only cache records
class BrokerHarness:

    # construction keeps each controller endpoint inside the run directory used by its worker
    def __init__(
        self,
        TmpPath: FilePath,
        RunName: str,
        PacketPath: FilePath,
        ModelName: str = "gpt-6.1-terra",
        SourceRoot: FilePath = KRepoRoot,
    ) -> None:
        super().__init__()
        self.RunPath = TmpPath / RunName
        self.Command, self.EnvValue = ProbeArgs(
            TmpPath, RunName, PacketPath, ModelName, "broker", SourceRoot=SourceRoot
        )
        self.ChildProc: StartProcess[str] | None = None

    # readiness is bounded so an initialization defect cannot hang the integration suite
    def __enter__(self) -> "BrokerHarness":
        self.ChildProc = StartProcess(
            self.Command,
            env=self.EnvValue,
            stdin=PipeStream,
            stdout=PipeStream,
            stderr=PipeStream,
            text=True,
        )
        Deadline = MonoTime() + 10
        while not (self.RunPath / "BrokerReady.json").is_file():
            if self.ChildProc.poll() is not None or MonoTime() >= Deadline:
                Output, Errors = self.ChildProc.communicate("stop\n", timeout=5)
                raise AssertionError(Output + Errors)
            WaitBriefly(0.01)
        return self

    # normal controller exit must close its provider and remove the authenticated ownership record
    def __exit__(
        self,
        ErrorType: type[BaseException] | None,
        ErrorValue: BaseException | None,
        ErrorTrace: TracebackType | None,
    ) -> None:
        if self.ChildProc is not None:
            Output, Errors = self.ChildProc.communicate("stop\n", timeout=10)
            assert self.ChildProc.returncode == 0, Output + Errors
            assert not (self.RunPath / "ProviderBroker.json").exists()
            assert (self.RunPath / "BrokerClosed.json").is_file()
