# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import re
from os import environ
from pathlib import Path
from shutil import which
from tempfile import mkdtemp
from threading import Event, Lock
from time import monotonic

from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import CheckComponents
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ValidateProgram
from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexPolicy import (
    ServerCommand,
    ThreadOptions,
)
from InferenceGrid.BuilderDevelopment.Generation.Transport.SessionProcess import (
    SessionProcess,
)


# repeated generation uses one owned provider process while each candidate receives a fresh conversation
class CodexSession:
    def __init__(
        self, Options, Directory=None, Command=None, AllowPersonalInstructions=False
    ):
        if (
            Options.provider != "codex"
            or Options.auth != "login"
            or not isinstance(Options.model, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", Options.model)
        ):
            raise ValueError(
                "provider_unavailable: persistent codex requires login and an explicit model"
            )
        self.options = Options
        if type(AllowPersonalInstructions) is not bool:
            raise ValueError(
                "provider_instruction_scope_missing: personal context permission must be explicit"
            )
        self.allow_personal_instructions = AllowPersonalInstructions
        self.directory = (
            CheckComponents(Directory)
            if Directory is not None
            else Path(mkdtemp(prefix="KitCodexSession-")).resolve()
        )
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if any(self.directory.iterdir()):
            raise ValueError(
                "persistent codex requires a fresh private session directory"
            )
        Executable = which("codex")
        if Command is None and Executable is None:
            raise ValueError("provider_unavailable: codex CLI is not installed")
        self.command = (
            list(Command) if Command is not None else ServerCommand(Executable)
        )
        self.process = None
        self.closed = Event()
        self.call_lock = Lock()
        self.counter, self.calls = 0, 0
        self.events = []
        self.instruction_sources = []
        self.ready = False

    # all protocol writes use the same request deadline and cannot silently accept tool requests
    def _send(self, Value, Deadline):
        if self.closed.is_set():
            raise OSError("provider_closed: owned codex session was closed")
        self.process.pipe.Send(Value, Deadline)

    # unsolicited capabilities fail closed rather than running a model requested command
    def _read(self, Deadline):
        Value = self.process.pipe.Receive(Deadline)
        self.events.append(Value)
        if Value.get("method") and Value.get("id") is not None:
            self._send(
                {
                    "id": Value["id"],
                    "error": {
                        "code": -32601,
                        "message": "Tools and approvals are unavailable",
                    },
                },
                Deadline,
            )
            raise ValueError(
                "provider_tools_forbidden: unsolicited codex server request"
            )
        if Value.get("method") in ("item/started", "item/completed"):
            Kind = Value.get("params", {}).get("item", {}).get("type")
            if Kind not in ("userMessage", "agentMessage", "reasoning"):
                raise ValueError(
                    "provider_tools_forbidden: codex attempted a tool item"
                )
        return Value

    # correlated replies allow notifications to arrive before or between response messages
    def _request(self, Method, Params, Deadline):
        self.counter += 1
        Identity = self.counter
        self._send({"id": Identity, "method": Method, "params": Params}, Deadline)
        while True:
            Value = self._read(Deadline)
            if Value.get("id") != Identity or Value.get("method"):
                continue
            if Value.get("error"):
                raise ValueError(
                    "provider_protocol_failed: " + json.dumps(Value["error"])[:1024]
                )
            if not isinstance(Value.get("result"), dict):
                raise ValueError(
                    "provider_protocol_failed: codex response lacks an object result"
                )
            return Value["result"]

    # startup and model capability checks consume the same bounded call time as inference
    def _start(self, Deadline):
        if self.closed.is_set():
            raise OSError("provider_closed: owned codex session was closed")
        if self.ready:
            return
        self.process = SessionProcess(self.command, self.options, self.directory)
        self._request(
            "initialize",
            {"clientInfo": {"name": "kit_builder_generation", "version": "1.0.0"}},
            Deadline,
        )
        self._send({"method": "initialized", "params": {}}, Deadline)
        Cursor, Found = None, False
        while True:
            Models = self._request(
                "model/list",
                {"limit": 100, **({"cursor": Cursor} if Cursor else {})},
                Deadline,
            )
            Found = Found or any(
                Item.get("id") == self.options.model
                or Item.get("model") == self.options.model
                for Item in Models.get("data", [])
                if isinstance(Item, dict)
            )
            Cursor = Models.get("nextCursor")
            if Found or not Cursor:
                break
        if not Found:
            raise ValueError(
                "provider_unavailable: pinned model is unavailable to the signed in account"
            )
        self.ready = True

    # actual per turn usage remains separate from unknown prices and cache reservations
    def _usage(self, ThreadId, TurnId):
        Usage = None
        for Value in self.events:
            Params = Value.get("params", {})
            if (
                Value.get("method") == "thread/tokenUsage/updated"
                and Params.get("threadId") == ThreadId
                and Params.get("turnId") == TurnId
            ):
                Usage = Params.get("tokenUsage", {}).get("last")
        Usage = Usage or {}
        if not all(
            type(Usage.get(Name)) is int and Usage[Name] >= 0
            for Name in (
                "inputTokens",
                "outputTokens",
                "cachedInputTokens",
                "totalTokens",
            )
        ):
            Usage = {}
        return {
            "input_tokens": Usage.get("inputTokens"),
            "output_tokens": Usage.get("outputTokens"),
            "cached_input_tokens": Usage.get("cachedInputTokens"),
            "total_tokens": Usage.get("totalTokens"),
            "reasoning_output_tokens": Usage.get("reasoningOutputTokens"),
            "cost_usd": None,
            "actual_model": self.options.model if ThreadId is not None else None,
            "model_identity_source": "thread/start" if ThreadId is not None else None,
            "accounting": "reported" if Usage else "unavailable",
        }

    # fixed options and isolated threads preserve bounded generation while amortizing provider startup
    def Generate(self, Prompt, Schema, Seconds):
        Started = monotonic()
        if (
            not isinstance(Prompt, str)
            or not 0 < len(Prompt.encode()) <= 128 * 1024
            or not isinstance(Schema, dict)
            or not 0 < Seconds <= 3600
        ):
            raise ValueError("provider_input_limit: invalid bounded generation request")
        Deadline = Started + Seconds
        if not self.call_lock.acquire(timeout=Seconds):
            raise TimeoutError("provider_timeout: codex session is busy")
        ThreadId, TurnId = None, None
        self.events = []
        Reused = self.calls > 0
        Result = {"status": "provider_protocol_failed"}
        try:
            if self.process is not None:
                self.process.pipe.seen = 0
            self._start(Deadline)
            Thread = self._request(
                "thread/start", ThreadOptions(self.options, self.directory), Deadline
            )
            CodexHome = Path(
                environ.get("CODEX_HOME", Path.home() / ".codex")
            ).resolve()
            Sources = Thread.get("instructionSources", [])
            if (
                Thread.get("model") != self.options.model
                or Thread.get("approvalPolicy") != "never"
                or Thread.get("sandbox", {}).get("type") != "readOnly"
                or Thread.get("sandbox", {}).get("networkAccess") is True
                or not isinstance(Sources, list)
                or any(
                    not isinstance(Source, str)
                    or Path(Source).resolve().parent != CodexHome
                    or Path(Source).name not in ("AGENTS.md", "AGENTS.override.md")
                    for Source in Sources
                )
            ):
                raise ValueError(
                    "provider_policy_failed: codex changed model permissions or instructions"
                )
            self.instruction_sources = Sources
            if Sources and not self.allow_personal_instructions:
                raise ValueError(
                    "provider_instruction_scope_missing: codex would include personal instruction files without explicit permission"
                )
            ThreadId = Thread["thread"]["id"]
            Turn = self._request(
                "turn/start",
                {
                    "threadId": ThreadId,
                    "input": [{"type": "text", "text": Prompt}],
                    "effort": "low",
                    "outputSchema": Schema,
                },
                Deadline,
            )
            TurnId = Turn["turn"]["id"]

            def Completed():
                return next(
                    (
                        Value["params"]["turn"]
                        for Value in self.events
                        if Value.get("method") == "turn/completed"
                        and Value.get("params", {}).get("threadId") == ThreadId
                        and Value.get("params", {}).get("turn", {}).get("id") == TurnId
                    ),
                    None,
                )

            while Completed() is None:
                self._read(Deadline)
            Completion = Completed()
            if Completion.get("status") != "completed":
                raise ValueError(
                    "provider_failed: " + json.dumps(Completion.get("error"))[:1024]
                )
            Replies = [
                Value["params"]["item"].get("text", "")
                for Value in self.events
                if Value.get("method") == "item/completed"
                and Value.get("params", {}).get("threadId") == ThreadId
                and Value.get("params", {}).get("turnId") == TurnId
                and Value.get("params", {}).get("item", {}).get("type")
                == "agentMessage"
            ]
            Candidate = ValidateProgram(json.loads(Replies[-1]))
            self._request("thread/unsubscribe", {"threadId": ThreadId}, Deadline)
            Result = {"status": "candidate", "candidate": Candidate}
            self.calls += 1
        except (
            OSError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            TimeoutError,
        ) as Error:
            Prefix = str(Error).split(":", 1)[0]
            if self.closed.is_set() and Prefix != "provider_cleanup_failed":
                Prefix = "provider_closed"
            Result = {
                "status": (
                    Prefix
                    if Prefix.startswith("provider_")
                    else "provider_protocol_failed"
                ),
                "reason": str(Error)[:2048],
            }
            try:
                self.close()
            except OSError as Cleanup:
                Result = {
                    "status": "provider_cleanup_failed",
                    "reason": str(Cleanup)[:2048],
                    "original_failure": Result,
                }
        finally:
            self.call_lock.release()
        Result.update(
            usage=self._usage(ThreadId, TurnId),
            command=self.command,
            exit_code=(
                None
                if not self.closed.is_set()
                else (
                    self.process.owner.process.returncode
                    if self.process and not self.process.owner.windows
                    else None
                )
            ),
            events=self.events,
            capture={
                "transport": "codex-app-server",
                "session_reused": Reused,
                "ephemeral_thread": ThreadId,
                "owned_server_pid": (
                    self.process.owner.process.pid if self.process else None
                ),
                "provider_output_bytes": (
                    self.process.pipe.seen if self.process and self.process.pipe else 0
                ),
                "elapsed_seconds": monotonic() - Started,
                "session_retained": not self.closed.is_set(),
                "instruction_sources": self.instruction_sources,
                "personal_instructions_authorized": self.allow_personal_instructions,
                "tools_enabled": False,
            },
        )
        return Result

    # the controller can cancel active inference without acquiring its generation lock
    def close(self):
        self.closed.set()
        if self.process is not None:
            self.process.close()
