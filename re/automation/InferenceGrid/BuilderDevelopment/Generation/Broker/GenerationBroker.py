# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hmac import compare_digest
from json import loads
from math import isfinite
from os import getpid, urandom
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket, timeout as SocketTimeout
from threading import Event, Lock, Thread
from time import monotonic
from uuid import uuid4

from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire import (
    ReadFrame,
    SendFrame,
)
from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerAuth import AuthProof
from InferenceGrid.BuilderDevelopment.Generation.Broker.OwnerIdentity import (
    OwnerIdentity,
)
from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import OwnedPath
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ProgramSchema
from Sessions import write_private


# the controller owns one provider process across workers without leaving a detached background service
class GenerationBroker:
    def __init__(
        self, Options, Directory, SessionFactory=None, AllowPersonalInstructions=False
    ):
        self.options = Options
        if type(AllowPersonalInstructions) is not bool:
            raise ValueError(
                "provider_instruction_scope_missing: personal instruction authorization must be explicit"
            )
        self.directory = Path(Directory)
        self.enabled = Options.provider == "codex" and Options.auth == "login"
        self.factory = SessionFactory
        self.personal_instructions = AllowPersonalInstructions
        self.session = None
        self.session_lock = Lock()
        self.failure = None
        self.stopped = Event()
        self.listener = None
        self.thread = None
        self.token = urandom(32).hex()
        self.path = OwnedPath(self.directory / "ProviderBroker.json", self.directory)

    # interrupted controllers leave evidence while live owners can never be displaced by a resume
    def Recover(self):
        if not self.path.exists():
            return
        if self.path.stat().st_size > 8192:
            raise ValueError(
                "provider_unavailable: invalid existing broker ownership record"
            )
        Record = loads(OwnedPath(self.path, self.directory).read_text(encoding="utf-8"))
        if (
            not isinstance(Record, dict)
            or Record.get("schema_version") != 1
            or type(Record.get("pid")) is not int
            or not 1 < Record["pid"] <= 0xFFFFFFFF
            or not isinstance(Record.get("pid_start"), str)
            or not Record["pid_start"]
        ):
            raise ValueError(
                "provider_unavailable: existing broker ownership cannot be verified"
            )
        if OwnerIdentity(Record["pid"]) == Record["pid_start"]:
            raise OSError(
                "provider_unavailable: another live controller owns the broker"
            )
        self.path.rename(
            OwnedPath(
                self.directory / ("ProviderBroker." + uuid4().hex + ".stale.json"),
                self.directory,
            )
        )

    # a private authenticated loopback listener lets short lived workers reuse the owned provider
    def __enter__(self):
        if not self.enabled:
            return self
        self.Recover()
        Identity = OwnerIdentity(getpid())
        if Identity is None:
            raise OSError(
                "provider_unavailable: controller process ownership cannot be inspected"
            )
        self.listener = socket(AF_INET, SOCK_STREAM)
        try:
            self.listener.bind(("127.0.0.1", 0))
            self.listener.listen(8)
            self.listener.settimeout(0.2)
            self.thread = Thread(
                target=self.Serve, name="builder-provider-broker", daemon=True
            )
            self.thread.start()
            write_private(
                self.path,
                {
                    "schema_version": 1,
                    "pid": getpid(),
                    "pid_start": Identity,
                    "host": "127.0.0.1",
                    "port": self.listener.getsockname()[1],
                    "token": self.token,
                    "provider": self.options.provider,
                    "auth": self.options.auth,
                    "model": self.options.model,
                    "personal_instructions": self.personal_instructions,
                },
            )
        except BaseException:
            self.close()
            raise
        return self

    # each request retains a fresh model thread while the transport process remains reusable
    def Serve(self):
        while not self.stopped.is_set():
            try:
                Connection, _ = self.listener.accept()
            except SocketTimeout:
                continue
            except OSError:
                if self.stopped.is_set():
                    return
                self.failure = "provider_unavailable: local broker listener failed"
                return
            with Connection:
                Deadline = monotonic() + 5
                try:
                    Hello = ReadFrame(Connection, 4096, Deadline)
                    if not isinstance(Hello, dict) or set(Hello) != {"hello"}:
                        raise ValueError(
                            "provider_unavailable: invalid local broker handshake"
                        )
                    ClientNonce = Hello["hello"]
                    ServerNonce = urandom(32).hex()
                    SendFrame(
                        Connection,
                        {
                            "nonce": ServerNonce,
                            "proof": AuthProof(
                                self.token, "server", ClientNonce, ServerNonce
                            ),
                        },
                        4096,
                        Deadline,
                    )
                    Message = ReadFrame(Connection, 256 * 1024, Deadline)
                    if (
                        not isinstance(Message, dict)
                        or set(Message) != {"proof", "request"}
                        or not isinstance(Message.get("proof"), str)
                        or not compare_digest(
                            Message["proof"],
                            AuthProof(
                                self.token,
                                "client",
                                ClientNonce,
                                ServerNonce,
                                Message.get("request"),
                            ),
                        )
                    ):
                        raise ValueError(
                            "provider_unavailable: local broker authentication failed"
                        )
                    Request = Message.get("request")
                    if not isinstance(Request, dict) or set(Request) != {
                        "provider",
                        "auth",
                        "model",
                        "prompt",
                        "schema",
                        "seconds",
                        "deadline",
                    }:
                        raise ValueError(
                            "provider_unavailable: invalid local broker request"
                        )
                    if any(
                        Request[Key] != getattr(self.options, Key)
                        for Key in ("provider", "auth", "model")
                    ):
                        raise ValueError(
                            "provider_unavailable: broker model or authentication differs from the saved job"
                        )
                    Seconds = Request["seconds"]
                    if (
                        type(Seconds) not in (int, float)
                        or not isfinite(Seconds)
                        or not 0 < Seconds <= 3600
                        or type(Request["deadline"]) not in (int, float)
                        or not isfinite(Request["deadline"])
                        or not isinstance(Request["prompt"], str)
                        or len(Request["prompt"].encode("utf-8")) > 128 * 1024
                        or Request["schema"] != ProgramSchema()
                    ):
                        raise ValueError(
                            "provider_unavailable: local broker request exceeds its contract"
                        )
                    Deadline = min(monotonic() + Seconds, Request["deadline"])
                    Seconds = Deadline - monotonic()
                    if Seconds <= 0:
                        raise TimeoutError(
                            "provider_timeout: queued broker request expired before execution"
                        )
                    if self.failure:
                        raise OSError(self.failure)
                    with self.session_lock:
                        if self.stopped.is_set():
                            raise OSError(
                                "provider_unavailable: controller broker is stopping"
                            )
                        if self.session is None:
                            Factory = self.factory
                            if Factory is None:
                                from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession import (
                                    CodexSession,
                                )

                                Created = CodexSession(
                                    self.options,
                                    AllowPersonalInstructions=self.personal_instructions,
                                )
                            else:
                                Created = Factory(self.options)
                            if self.stopped.is_set():
                                Created.close()
                                raise OSError(
                                    "provider_unavailable: controller broker stopped during initialization"
                                )
                            self.session = Created
                        Session = self.session
                    Remaining = Deadline - monotonic()
                    if Remaining <= 0:
                        raise TimeoutError(
                            "provider_timeout: broker initialization exhausted the request deadline"
                        )
                    Response = Session.Generate(
                        Request["prompt"], Request["schema"], Remaining
                    )
                    SendFrame(
                        Connection, {"response": Response}, 8 * 1024 * 1024, Deadline
                    )
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    TimeoutError,
                ) as Error:
                    Message = str(Error)
                    if isinstance(Error, TimeoutError) and not Message.startswith(
                        "provider_timeout"
                    ):
                        Message = "provider_timeout: " + Message
                    try:
                        SendFrame(
                            Connection, {"error": Message[:2048]}, 8192, monotonic() + 1
                        )
                    except (OSError, ValueError, TimeoutError):
                        pass

    # shutdown closes the owned application before releasing its authenticated endpoint record
    def close(self):
        self.stopped.set()
        if self.listener is not None:
            self.listener.close()
        Failure = None
        Session = None
        if self.session_lock.acquire(timeout=5):
            try:
                Session = self.session
            finally:
                self.session_lock.release()
        else:
            Failure = OSError(
                "provider_cleanup_failed: local broker session initialization did not stop"
            )
        if Session is not None:
            try:
                Session.close()
            except (OSError, ValueError, TimeoutError) as Error:
                Failure = Error
        if self.thread is not None:
            self.thread.join(timeout=6)
            if self.thread.is_alive() and Failure is None:
                Failure = OSError("provider_cleanup_failed: local broker did not stop")
        if Failure is None and self.path.is_file():
            try:
                Record = loads(
                    OwnedPath(self.path, self.directory).read_text(encoding="utf-8")
                )
                if isinstance(Record, dict) and Record.get("token") == self.token:
                    self.path.unlink()
            except (OSError, ValueError, TypeError):
                pass
        if Failure is not None:
            raise OSError("provider_cleanup_failed: " + str(Failure)) from Failure

    # context ownership keeps all provider teardown inside the controller error boundary
    def __exit__(self, *Details):
        self.close()
