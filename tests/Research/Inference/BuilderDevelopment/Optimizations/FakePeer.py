# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from collections.abc import Callable
from json import dumps as EncodeJson
from typing import cast as TypeCast
from os import getpid as ProcessId, urandom as RandomBytes
from pathlib import Path as FilePath
from socket import AF_INET as InetFamily, SOCK_STREAM as StreamKind, socket as NewSocket
from sys import argv as CliArgs, path as SearchPaths

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadConfig,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# a live unrelated process reproduces a reused local port without receiving an authorized generation request
def MainPeer() -> None:
    ConfigValue = ReadConfig(ResolveTemp(CliArgs[1]).read_bytes())
    RepoRoot = FilePath(__file__).resolve().parents[5]
    SearchPaths[:0] = [str(RepoRoot / "re/automation"), str(RepoRoot)]
    OwnerIdentity = TypeCast(
        Callable[[int], str | None],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.OwnerIdentity",
            "OwnerIdentity",
        ),
    )
    from tests.Research.Inference.BuilderDevelopment.Optimizations.FakeProof import (
        SendBadProof,
    )

    RunPath = FilePath(ConfigValue["run_root"])
    with NewSocket(InetFamily, StreamKind) as Listener:
        Listener.bind(("127.0.0.1", 0))
        Listener.listen(1)
        Listener.settimeout(10)
        Record: dict[str, object] = {
            "schema_version": 1,
            "pid": ProcessId(),
            "pid_start": OwnerIdentity(ProcessId()),
            "host": "127.0.0.1",
            "port": Listener.getsockname()[1],
            "token": RandomBytes(32).hex(),
            "provider": "codex",
            "auth": "login",
            "model": ConfigValue["model"],
            "personal_instructions": False,
        }
        _ = (RunPath / "ProviderBroker.json").write_text(
            EncodeJson(Record), encoding="utf-8"
        )
        _ = (RunPath / "PeerReady.json").write_text("{}", encoding="utf-8")
        ResultValue = SendBadProof(Listener)
    _ = (RunPath / "PeerFrames.json").write_text(
        EncodeJson(ResultValue), encoding="utf-8"
    )
