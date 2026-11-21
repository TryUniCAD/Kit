# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import contextmanager
from json import dumps, loads
from math import isfinite
from os import O_CREAT, O_EXCL, O_WRONLY, close, open as OpenFile, replace
from pathlib import Path
from time import time
from uuid import uuid4


# a shared durable reservation prevents parallel or resumed jobs from spending the same call budget
@contextmanager
def BudgetLock(StatePath):
    LockPath = StatePath.with_name(StatePath.name + ".lock")
    try:
        Descriptor = OpenFile(LockPath, O_CREAT | O_EXCL | O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(
            "model budget is locked by another or interrupted reservation"
        ) from None
    close(Descriptor)
    try:
        yield
    finally:
        LockPath.unlink()


# budget writes replace only the owned state snapshot rather than overwriting unknown temporary files
def SaveBudget(StatePath, State):
    Temporary = StatePath.with_name(StatePath.name + "." + uuid4().hex)
    try:
        with Temporary.open("x", encoding="utf-8") as Output:
            Output.write(dumps(State, indent=2, sort_keys=True, allow_nan=False) + "\n")
        replace(Temporary, StatePath)
    finally:
        Temporary.unlink(missing_ok=True)


# configured bounds are checked before any provider process or network connection starts
def CheckLimits(Budget, Options):
    if not isinstance(Budget, dict) or Budget.get("authorized") is not True:
        raise ValueError("automatic builder generation is not authorized")
    for Name in ("max_calls", "call_seconds", "max_seconds"):
        if type(Budget.get(Name)) is not int or not 1 <= Budget[Name] <= 86400:
            raise ValueError("model budget requires positive bounded " + Name)
    for Name in ("max_total_tokens", "max_output_tokens"):
        if Budget.get(Name) is not None and (
            type(Budget[Name]) is not int or Budget[Name] < 1
        ):
            raise ValueError("invalid model token bound " + Name)
    Cost = Budget.get("max_cost_usd")
    if Cost is not None and (
        type(Cost) not in (int, float) or not isfinite(Cost) or Cost < 0
    ):
        raise ValueError("invalid model cost bound")
    if Options is None or Options.provider not in ("codex", "claude", "ollama"):
        raise ValueError("configured model provider is required")
    if type(Options.calls) is not int or Options.calls < 1:
        raise ValueError("configured model provider must bound its call count")
    if Options.provider != "ollama" and (
        Cost is not None
        or Budget.get("max_total_tokens") is not None
        or Budget.get("max_output_tokens") is not None
    ):
        raise ValueError(
            "provider_budget_capability_missing: CLI cannot prebound billed tokens or monetary cost"
        )
    if Options.provider == "ollama" and Options.auth != "local":
        raise ValueError("Ollama generation requires explicitly local authentication")


# started calls consume their reservation even if interruption hides final provider usage
def ReserveCall(Budget, Options, Directory):
    CheckLimits(Budget, Options)
    StatePath = Path(
        Budget.get("state_path", Path(Directory).parent / "ModelBudget.json")
    ).resolve()
    StatePath.parent.mkdir(parents=True, exist_ok=True)
    if StatePath.is_symlink():
        raise ValueError("model budget state must not be a symlink")
    with BudgetLock(StatePath):
        State = (
            loads(StatePath.read_text())
            if StatePath.exists()
            else {"schema_version": 1, "started_at": time(), "calls": []}
        )
        if State.get("schema_version") != 1 or not isinstance(State.get("calls"), list):
            raise ValueError("invalid model budget state")
        Spent = sum(
            Call.get(
                "elapsed_seconds", Call.get("reserved_seconds", Budget["call_seconds"])
            )
            for Call in State["calls"]
        )
        Remaining = Budget["max_seconds"] - Spent
        if Remaining < 1 or len(State["calls"]) >= min(
            Budget["max_calls"], Options.calls
        ):
            raise ValueError("model_budget_exhausted")
        if Budget.get("max_total_tokens") is not None:
            if any(
                Call.get("usage", {}).get("total_tokens") is None
                for Call in State["calls"]
            ):
                raise ValueError(
                    "model_usage_unknown: cannot reserve another token-bounded call"
                )
            Used = sum(Call["usage"]["total_tokens"] for Call in State["calls"])
            if Used >= Budget["max_total_tokens"]:
                raise ValueError("model_token_budget_exhausted")
        else:
            Used = 0
        CallId = uuid4().hex
        Seconds = max(1, min(Budget["call_seconds"], int(Remaining)))
        State["calls"].append(
            {
                "id": CallId,
                "started_at": time(),
                "reserved_seconds": Seconds,
                "status": "started",
                "directory": str(Directory),
                "provider": Options.provider,
                "auth": Options.auth,
                "model": Options.model,
            }
        )
        SaveBudget(StatePath, State)
    return {
        "id": CallId,
        "state_path": str(StatePath),
        "seconds": Seconds,
        "output_tokens": (
            None
            if Options.provider != "ollama"
            else min(
                Budget.get("max_output_tokens") or 1024,
                max(1, (Budget.get("max_total_tokens") or 2**31) - Used),
            )
        ),
        "remaining_tokens": (
            None
            if Budget.get("max_total_tokens") is None
            else Budget["max_total_tokens"] - Used
        ),
    }


# final accounting preserves actual provider usage and records unknown costs without inventing a charge
def FinishCall(Reservation, Status, Usage, Elapsed):
    StatePath = Path(Reservation["state_path"])
    with BudgetLock(StatePath):
        State = loads(StatePath.read_text())
        Matching = [Call for Call in State["calls"] if Call["id"] == Reservation["id"]]
        if len(Matching) != 1 or Matching[0]["status"] != "started":
            raise ValueError("model reservation is no longer current")
        Matching[0].update(
            status=Status, finished_at=time(), elapsed_seconds=Elapsed, usage=Usage
        )
        SaveBudget(StatePath, State)
