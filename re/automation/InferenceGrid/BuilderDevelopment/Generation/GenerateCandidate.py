# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from subprocess import TimeoutExpired
from time import monotonic

from InferenceGrid.BuilderDevelopment.Generation.Cache.RequestCache import RequestCache
from InferenceGrid.BuilderDevelopment.Generation.Cache.ReuseCandidate import (
    PublishReuse,
)
from InferenceGrid.BuilderDevelopment.Generation.Broker.CallBroker import CallBroker
from InferenceGrid.BuilderDevelopment.Generation.GenerationBudget import (
    CheckLimits,
    FinishCall,
    ReserveCall,
)
from InferenceGrid.BuilderDevelopment.Generation.GenerationPacket import (
    BuildPrompt,
    GenerationPacket,
    WriteArtifact,
)
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import (
    ProgramSchema,
    ValidateProgram,
)
from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import (
    ArtifactHash,
    OwnedPath,
)
from InferenceGrid.BuilderDevelopment.Generation.ProviderTransport import (
    CallCli,
    CallOllama,
    ProviderExecutable,
)


# failures identify unavailable generation separately from defects observed later by the native verifier
def FailureClass(Error):
    Message = str(Error)
    for Prefix in (
        "provider_unavailable",
        "provider_timeout",
        "provider_protocol_failed",
        "provider_policy_failed",
        "provider_tools_forbidden",
        "provider_context_limit",
        "provider_context_changed",
        "provider_closed",
        "provider_input_limit",
        "provider_budget_capability_missing",
        "model_budget_exhausted",
        "model_token_budget_exhausted",
        "model_usage_unknown",
        "provider_cleanup_failed",
        "provider_output_limit",
        "provider_instruction_scope_missing",
        "generation_cache_invalid",
        "generation_cache_unavailable",
    ):
        if Message.startswith(Prefix):
            return Prefix
    if isinstance(Error, (TimeoutError, TimeoutExpired)):
        return "provider_timeout"
    if "authorized" in Message:
        return "generation_not_authorized"
    return "invalid_generation"


# every started provider attempt retains source inputs actual outputs and independent typed validation
def GenerateUncached(Packet, Options, Directory, Budget):
    Started = monotonic()
    Reservation, Artifacts = None, {}
    Usage = {
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "cost_usd": None,
        "accounting": "unavailable",
    }
    Result = {
        "status": "blocked",
        "classification": "generation_not_authorized",
        "usage": Usage,
    }
    try:
        CheckLimits(Budget, Options)
        ProviderExecutable(Options)
        CleanPacket, PacketPin = GenerationPacket(Packet)
        Prompt = BuildPrompt(CleanPacket)
        Target = OwnedPath(Directory, Budget["run_root"])
        Target.mkdir(mode=0o700, parents=True, exist_ok=True)
        Target = OwnedPath(Directory, Budget["run_root"])
        if any(Target.iterdir()):
            raise ValueError("generation requires a fresh private attempt directory")
        Schema = ProgramSchema()
        Artifacts["packet"] = WriteArtifact(Target / "Packet.json", CleanPacket)
        Artifacts["schema"] = WriteArtifact(Target / "Schema.json", Schema)
        RawPrompt = Prompt.encode("utf-8")
        with (Target / "Prompt.txt").open("xb") as Output:
            Output.write(RawPrompt)
        Artifacts["prompt"] = {
            "path": str(Target / "Prompt.txt"),
            "sha256": sha256(RawPrompt).hexdigest(),
            "size_bytes": len(RawPrompt),
        }
        Reservation = ReserveCall(Budget, Options, Target)
        Artifacts["request"] = WriteArtifact(
            Target / "Request.json",
            {
                "schema_version": 1,
                "packet_sha256": PacketPin,
                "reservation": Reservation,
                "provider": Options.provider,
                "auth": Options.auth,
                "model": Options.model or "cli-default",
                "limits": {
                    Key: Value
                    for Key, Value in Budget.items()
                    if Key not in {"state_path"}
                },
                "tools_enabled": False,
                "reserved_qualification_disclosed": False,
            },
        )
        if (
            Options.provider == "codex"
            and Options.auth == "login"
            and Budget.get("broker_path")
        ):
            Response = CallBroker(
                Options,
                Prompt,
                Schema,
                Target,
                Reservation,
                Budget["broker_path"],
                Budget.get("personal_instructions", False),
            )
        else:
            Response = (CallOllama if Options.provider == "ollama" else CallCli)(
                Options, Prompt, Schema, Target, Reservation
            )
        Usage = Response["usage"]
        Result = {
            "status": "failed",
            "classification": Response["status"],
            "usage": Usage,
            "command": Response["command"],
            "exit_code": Response.get("exit_code"),
        }
        if Response["status"] == "candidate":
            Program = ValidateProgram(Response["candidate"])
            Artifacts["candidate"] = WriteArtifact(Target / "Candidate.json", Program)
            Result.update(
                status="candidate",
                classification="candidate_generated",
                program=Program,
            )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        TimeoutError,
        TimeoutExpired,
    ) as Error:
        Result = {
            "status": "failed" if Reservation is not None else "blocked",
            "classification": FailureClass(Error),
            "reason": str(Error)[:2048],
            "usage": Usage,
        }
    finally:
        if Reservation is not None:
            try:
                FinishCall(Reservation, Result["status"], Usage, monotonic() - Started)
            except (OSError, ValueError, KeyError, TypeError) as Error:
                Result = {
                    "status": "blocked",
                    "classification": "model_accounting_failed",
                    "reason": str(Error)[:2048],
                    "usage": Usage,
                }
    Result["elapsed_seconds"] = monotonic() - Started
    Result["artifact_paths"] = Artifacts
    if Reservation is not None:
        try:
            Target = OwnedPath(Directory, Budget["run_root"])
            for Name in ("Provider.jsonl", "Response.json", "ProviderCapture.json"):
                FilePath = OwnedPath(Target / Name, Budget["run_root"])
                if FilePath.is_file():
                    Artifacts[Name] = ArtifactHash(FilePath, Budget["run_root"])
            WriteArtifact(Target / "Generation.json", Result)
        except (OSError, ValueError) as Error:
            Result.update(
                status="blocked",
                classification="generation_artifact_invalid",
                reason=str(Error)[:2048],
            )
    return Result


# coalescing happens before reservation so identical concurrent requests spend one model call
def GenerateCandidate(Packet, Options, Directory, Budget):
    Started = monotonic()
    try:
        CheckLimits(Budget, Options)
        CleanPacket, PacketPin = GenerationPacket(Packet)
        Schema = ProgramSchema()
        with RequestCache(Budget, PacketPin, Options, Schema) as Cache:
            Hit = Cache.Hit()
            if Hit is not None:
                return PublishReuse(
                    Hit,
                    CleanPacket,
                    PacketPin,
                    Options,
                    Directory,
                    Budget,
                    Schema,
                    Started,
                )
            Result = GenerateUncached(CleanPacket, Options, Directory, Budget)
            if Cache.enabled and Result.get("status") == "candidate":
                Publication = {
                    "hit": False,
                    "key": Cache.key,
                    "wait_seconds": Cache.wait_seconds,
                }
                try:
                    Cache.Store(
                        Result, PacketPin, Result["artifact_paths"]["prompt"]["sha256"]
                    )
                    Publication["published"] = Cache.Read() is not None
                except (OSError, ValueError, TypeError, KeyError) as Error:
                    Publication.update(published=False, error=str(Error)[:2048])
                Result["cache"] = Publication
                Result["artifact_paths"]["cache"] = WriteArtifact(
                    OwnedPath(Directory, Budget["run_root"]) / "CachePublication.json",
                    Publication,
                )
            return Result
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        TimeoutError,
        TimeoutExpired,
    ) as Error:
        Classification = FailureClass(Error)
        if Classification == "invalid_generation":
            Classification = "generation_cache_unavailable"
        return {
            "status": "blocked",
            "classification": Classification,
            "reason": str(Error)[:2048],
            "elapsed_seconds": monotonic() - Started,
            "usage": {
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
                "accounting": "unavailable",
            },
            "artifact_paths": {},
        }
