# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps, loads
from math import isfinite
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, run
from time import monotonic

from CodexAdvice.OllamaCall import post_local
from CodexAdvice.ProviderEnv import provider_env


# unavailable executables are a provider blocker rather than a generated builder defect
def ProviderExecutable(Options):
    if Options.provider == "ollama":
        return None
    Executable = which(Options.provider)
    if Executable is None:
        raise ValueError("provider_unavailable: configured model CLI is not installed")
    return Executable


# the existing advice transport policy is retained while the response schema becomes a builder program
def CodexCommand(Executable, Options, Directory):
    return [
        Executable,
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "apps",
        "--disable",
        "plugins",
        "--disable",
        "multi_agent",
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        *(("--model", Options.model) if Options.model is not None else ()),
        "--output-schema",
        str(Directory / "Schema.json"),
        "--output-last-message",
        str(Directory / "Response.json"),
        "--json",
        "-",
    ]


# claude uses the same tools-disabled authentication boundary as the existing decoding advice path
def ClaudeCommand(Executable, Options, Schema):
    return [
        Executable,
        "--print",
        "--safe-mode",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--disallowedTools",
        "mcp__*",
        "--no-session-persistence",
        "--max-turns",
        "3",
        *(("--model", Options.model) if Options.model is not None else ()),
        "--output-format",
        "json",
        "--json-schema",
        dumps(Schema),
    ]


# provider output is retained privately and never executed as code
def CallCli(Options, Prompt, Schema, Directory, Reservation):
    Executable = ProviderExecutable(Options)
    Command = (
        CodexCommand(Executable, Options, Directory)
        if Options.provider == "codex"
        else ClaudeCommand(Executable, Options, Schema)
    )
    RawPath = Directory / "Provider.jsonl"
    with RawPath.open("xb") as Output:
        Result = run(
            Command,
            input=Prompt,
            encoding="utf-8",
            cwd=Directory,
            stdout=Output,
            stderr=DEVNULL,
            env=provider_env(Options),
            timeout=Reservation["seconds"],
            check=False,
        )
    if RawPath.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("provider_response_too_large")
    Events = []
    for Line in RawPath.read_text(encoding="utf-8").splitlines():
        try:
            Event = loads(Line)
        except ValueError:
            continue
        if isinstance(Event, dict):
            Events.append(Event)
    Usage = ReadUsage(Options.provider, Events)
    if Result.returncode:
        return {
            "status": "provider_failed",
            "exit_code": Result.returncode,
            "usage": Usage,
            "command": Command,
        }
    if Options.provider == "claude":
        Response = next(
            (Event for Event in reversed(Events) if "structured_output" in Event), None
        )
        if Response is None or Response.get("is_error"):
            return {
                "status": "invalid_response",
                "exit_code": 0,
                "usage": Usage,
                "command": Command,
            }
        Candidate = Response["structured_output"]
        (Directory / "Response.json").write_text(
            dumps(Candidate, indent=2) + "\n", encoding="utf-8"
        )
    else:
        ResponsePath = Directory / "Response.json"
        if (
            ResponsePath.is_symlink()
            or not ResponsePath.is_file()
            or ResponsePath.stat().st_size > 8192
        ):
            return {
                "status": "invalid_response",
                "exit_code": 0,
                "usage": Usage,
                "command": Command,
            }
        try:
            Candidate = loads(ResponsePath.read_text(encoding="utf-8"))
        except ValueError:
            return {
                "status": "invalid_response",
                "exit_code": 0,
                "usage": Usage,
                "command": Command,
            }
    return {
        "status": "candidate",
        "candidate": Candidate,
        "usage": Usage,
        "command": Command,
        "exit_code": 0,
    }


# actual json event usage is recorded separately from limits and never guessed from answer length
def ReadUsage(Provider, Events):
    Input, Output, Cached, Cost, Model = None, None, None, None, None
    for Event in Events:
        if isinstance(Event.get("model"), str):
            Model = Event["model"]
        Value = Event.get("usage")
        if not isinstance(Value, dict):
            continue
        if Provider == "codex" and Event.get("type") != "turn.completed":
            continue
        InputValue = Value.get("input_tokens")
        if Provider == "claude":
            Parts = [
                Value.get(Name, 0)
                for Name in (
                    "input_tokens",
                    "cache_read_input_tokens",
                    "cache_creation_input_tokens",
                )
            ]
            InputValue = (
                sum(Parts)
                if all(type(Part) is int and Part >= 0 for Part in Parts)
                else None
            )
        Values = (
            InputValue,
            Value.get("output_tokens"),
            Value.get("cached_input_tokens", Value.get("cache_read_input_tokens", 0)),
        )
        if all(type(Item) is int and Item >= 0 for Item in Values):
            Input, Output, Cached = Values
        Amount = Event.get("total_cost_usd")
        if type(Amount) in (int, float) and isfinite(Amount) and Amount >= 0:
            Cost = Amount
    return {
        "input_tokens": Input,
        "output_tokens": Output,
        "cached_input_tokens": Cached,
        "total_tokens": None if Input is None or Output is None else Input + Output,
        "cost_usd": Cost,
        "actual_model": Model,
        "accounting": "reported" if Input is not None else "unavailable",
    }


# loopback local inference retains the existing remote-model rejection and adds explicit output limits
def CallOllama(Options, Prompt, Schema, Directory, Reservation):
    Started = monotonic()
    Metadata = post_local("/api/show", {"model": Options.model}, Reservation["seconds"])
    if (
        not isinstance(Metadata, dict)
        or not Metadata.get("model_info")
        or any(Metadata.get(Key) for Key in ("remote_host", "remote_model"))
    ):
        raise ValueError(
            "provider_unavailable: Ollama must identify an installed local model"
        )
    Remaining = Reservation["seconds"] - (monotonic() - Started)
    if Remaining <= 0:
        raise TimeoutError("provider time budget exhausted")
    InputBound = len(Prompt.encode("utf-8")) + 16
    OutputLimit = Reservation["output_tokens"]
    TokenLimit = Reservation["remaining_tokens"]
    if TokenLimit is not None:
        OutputLimit = min(OutputLimit, TokenLimit - InputBound)
        if OutputLimit < 1:
            raise ValueError(
                "model_token_budget_exhausted: conservative raw prompt bound does not fit"
            )
    Response = post_local(
        "/api/generate",
        {
            "model": Options.model,
            "prompt": Prompt,
            "raw": True,
            "format": Schema,
            "stream": False,
            "options": {
                "num_predict": OutputLimit,
                "num_ctx": InputBound + OutputLimit,
            },
        },
        Remaining,
    )
    with (Directory / "Provider.jsonl").open("x", encoding="utf-8") as OutputFile:
        OutputFile.write(dumps(Response, sort_keys=True) + "\n")
    if not isinstance(Response, dict) or Response.get("done") is not True:
        raise ValueError("provider did not complete local generation")
    Candidate = loads(Response["response"])
    (Directory / "Response.json").write_text(
        dumps(Candidate, indent=2) + "\n", encoding="utf-8"
    )
    Input, Output = Response.get("prompt_eval_count"), Response.get("eval_count")
    if any(type(Value) is not int or Value < 0 for Value in (Input, Output)):
        raise ValueError("local provider omitted token accounting")
    return {
        "status": "candidate",
        "candidate": Candidate,
        "command": ["ollama:loopback:/api/generate"],
        "usage": {
            "input_tokens": Input,
            "output_tokens": Output,
            "cached_input_tokens": None,
            "total_tokens": Input + Output,
            "cost_usd": 0.0,
            "actual_model": Response.get("model", Options.model),
            "accounting": "reported_local",
        },
    }
