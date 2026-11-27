# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import Popen as ChildProc
from time import monotonic as MonoTime, sleep as WaitBriefly


# a lock contender must remain unspent beyond measured provider turnaround before its owner is terminated
def ProveBlocked(
    Worker: ChildProc[str], TmpPath: FilePath, NormalSeconds: float
) -> None:
    ProviderPath = TmpPath / "ProviderCalls.jsonl"
    BudgetPath = TmpPath / "Waiting/ModelBudget.json"
    ProviderBytes = ProviderPath.read_bytes()
    BudgetBytes = BudgetPath.read_bytes()
    ReadyPath = TmpPath / "Waiting/Attempt.Ready.json"
    Deadline = MonoTime() + 10
    while not ReadyPath.is_file():
        assert Worker.poll() is None
        assert MonoTime() < Deadline
        WaitBriefly(0.01)
    Deadline = MonoTime() + NormalSeconds + 0.5
    while MonoTime() < Deadline:
        assert Worker.poll() is None
        assert ProviderPath.read_bytes() == ProviderBytes
        assert BudgetPath.read_bytes() == BudgetBytes
        WaitBriefly(0.02)
    assert Worker.poll() is None
    assert ProviderPath.read_bytes() == ProviderBytes
    assert BudgetPath.read_bytes() == BudgetBytes
