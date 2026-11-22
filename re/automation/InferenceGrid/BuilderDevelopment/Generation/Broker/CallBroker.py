# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps, loads
from hmac import compare_digest
from os import urandom
from pathlib import Path
from socket import create_connection
from time import monotonic

from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire import (
    ReadFrame,
    SendFrame,
)
from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerAuth import AuthProof
from InferenceGrid.BuilderDevelopment.Generation.Broker.OwnerIdentity import (
    OwnerIdentity,
)
from InferenceGrid.BuilderDevelopment.Generation.GenerationPacket import WriteArtifact
from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import OwnedPath


# workers can call only their controller broker and never choose an arbitrary remote endpoint
def CallBroker(
    Options,
    Prompt,
    Schema,
    Directory,
    Reservation,
    BrokerPath,
    AllowPersonalInstructions=False,
):
    Target = OwnedPath(BrokerPath, Reservation["run_root"])
    if not Target.is_file() or Target.stat().st_size > 8192:
        raise OSError("provider_unavailable: controller broker is not ready")
    try:
        Record = loads(Target.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as Error:
        raise OSError(
            "provider_unavailable: broker ownership record could not be read"
        ) from Error
    if not isinstance(Record, dict):
        raise ValueError(
            "provider_unavailable: broker ownership record is not an object"
        )
    if (
        Record.get("schema_version") != 1
        or Record.get("host") != "127.0.0.1"
        or type(Record.get("port")) is not int
        or not 1 <= Record["port"] <= 65535
        or not isinstance(Record.get("token"), str)
        or len(Record["token"]) != 64
    ):
        raise ValueError(
            "provider_unavailable: invalid controller broker ownership record"
        )
    if any(
        Record.get(Key) != getattr(Options, Key)
        for Key in ("provider", "auth", "model")
    ):
        raise ValueError(
            "provider_unavailable: controller broker model differs from the saved job"
        )
    if Record.get("personal_instructions", False) is not AllowPersonalInstructions:
        raise ValueError(
            "provider_unavailable: controller instruction authorization differs from the saved job"
        )
    if (
        type(Record.get("pid")) is not int
        or not 1 < Record["pid"] <= 0xFFFFFFFF
        or not isinstance(Record.get("pid_start"), str)
        or OwnerIdentity(Record["pid"]) != Record["pid_start"]
    ):
        raise OSError(
            "provider_unavailable: controller broker ownership is stale or uncertain"
        )
    Started = monotonic()
    Deadline = Started + Reservation["seconds"]
    try:
        with create_connection(
            (Record["host"], Record["port"]), timeout=min(5, Reservation["seconds"])
        ) as Connection:
            ClientNonce = urandom(32).hex()
            SendFrame(Connection, {"hello": ClientNonce}, 4096, Deadline)
            Challenge = ReadFrame(Connection, 4096, Deadline)
            if (
                not isinstance(Challenge, dict)
                or set(Challenge) != {"nonce", "proof"}
                or not isinstance(Challenge["proof"], str)
                or not compare_digest(
                    Challenge["proof"],
                    AuthProof(
                        Record["token"], "server", ClientNonce, Challenge["nonce"]
                    ),
                )
            ):
                raise OSError(
                    "provider_unavailable: local peer did not prove broker ownership"
                )
            Request = {
                "provider": Options.provider,
                "auth": Options.auth,
                "model": Options.model,
                "prompt": Prompt,
                "schema": Schema,
                "seconds": max(0.001, Deadline - monotonic()),
                "deadline": Deadline,
            }
            SendFrame(
                Connection,
                {
                    "proof": AuthProof(
                        Record["token"],
                        "client",
                        ClientNonce,
                        Challenge["nonce"],
                        Request,
                    ),
                    "request": Request,
                },
                256 * 1024,
                Deadline,
            )
            Reply = ReadFrame(Connection, 8 * 1024 * 1024, Deadline)
    except TimeoutError as Error:
        raise TimeoutError(
            "provider_timeout: controller broker request expired"
        ) from Error
    except (OSError, ValueError, TypeError, KeyError) as Error:
        raise OSError(
            "provider_protocol_failed: controller broker transport failed"
        ) from Error
    if not isinstance(Reply, dict):
        raise ValueError("provider_unavailable: invalid controller broker response")
    if "error" in Reply:
        Message = Reply["error"]
        if not isinstance(Message, str) or not Message.startswith("provider_"):
            raise OSError(
                "provider_protocol_failed: controller broker rejected the request"
            )
        if Message.startswith("provider_timeout"):
            raise TimeoutError(Message)
        raise OSError(Message)
    Response = Reply.get("response")
    if (
        not isinstance(Response, dict)
        or not isinstance(Response.get("status"), str)
        or not isinstance(Response.get("usage"), dict)
    ):
        raise ValueError("provider_unavailable: invalid provider response from broker")
    Events = Response.pop("events", [])
    if not isinstance(Events, list) or any(
        not isinstance(Event, dict) for Event in Events
    ):
        raise ValueError("provider_protocol_failed: invalid provider event records")
    Raw = "".join(
        dumps(Event, ensure_ascii=False, separators=(",", ":")) + "\n"
        for Event in Events
    ).encode("utf-8")
    if len(Raw) > 4 * 1024 * 1024:
        raise ValueError(
            "provider_output_limit: persistent provider events exceed their bound"
        )
    with OwnedPath(Path(Directory) / "Provider.jsonl", Reservation["run_root"]).open(
        "xb"
    ) as Output:
        Output.write(Raw)
    if Response.get("status") == "candidate":
        WriteArtifact(
            OwnedPath(Path(Directory) / "Response.json", Reservation["run_root"]),
            Response["candidate"],
        )
    WriteArtifact(
        OwnedPath(Path(Directory) / "ProviderCapture.json", Reservation["run_root"]),
        {
            "transport": "controller-owned-app-server",
            "elapsed_seconds": monotonic() - Started,
            "capture": Response.get("capture"),
            "model": Options.model,
            "tools_enabled": False,
        },
    )
    return Response
