# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from subprocess import TimeoutExpired
from time import monotonic

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
        "provider_budget_capability_missing",
        "model_budget_exhausted",
        "model_token_budget_exhausted",
        "model_usage_unknown",
    ):
        if Message.startswith(Prefix):
            return Prefix
    if isinstance(Error, (TimeoutError, TimeoutExpired)):
        return "provider_timeout"
    if "authorized" in Message:
        return "generation_not_authorized"
    return "invalid_generation"


# every started provider attempt retains source inputs actual outputs and independent typed validation
def GenerateCandidate(Packet, Options, Directory, Budget):
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
        Target = Path(Directory).resolve()
        if Target.is_symlink():
            raise ValueError("generation attempt directory must not be a symlink")
        Target.mkdir(parents=True, exist_ok=True)
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
        Target = Path(Directory).resolve()
        for Name in ("Provider.jsonl", "Response.json"):
            FilePath = Target / Name
            if FilePath.is_file() and not FilePath.is_symlink():
                Raw = FilePath.read_bytes()
                Artifacts[Name] = {
                    "path": str(FilePath),
                    "sha256": sha256(Raw).hexdigest(),
                    "size_bytes": len(Raw),
                }
        WriteArtifact(Target / "Generation.json", Result)
    return Result
