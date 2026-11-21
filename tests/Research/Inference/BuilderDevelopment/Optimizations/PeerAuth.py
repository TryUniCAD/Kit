# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from hmac import compare_digest as SameProof
from socket import socket as SocketType
from typing import cast as TypeCast
from os import urandom as RandomBytes
from time import monotonic as MonoTime

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    AsRecord,
    TextField,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# authenticated fixture peers prove broker rejection without placing its private token on the wire
def PeerRequest(
    Connection: SocketType,
    Record: dict[str, object],
    RequestValue: dict[str, object],
    IsWrong: bool = False,
) -> dict[str, object]:
    AuthProof = TypeCast(
        Callable[[str, str, str, str, object], str],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerAuth", "AuthProof"
        ),
    )
    ReadFrame = TypeCast(
        Callable[[SocketType, int, float], object],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire", "ReadFrame"
        ),
    )
    SendFrame = TypeCast(
        Callable[[SocketType, object, int, float], None],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire", "SendFrame"
        ),
    )

    ClientNonce = RandomBytes(32).hex()
    Deadline = MonoTime() + 8
    SendFrame(Connection, {"hello": ClientNonce}, 8192, Deadline)
    Challenge = AsRecord(ReadFrame(Connection, 8192, Deadline))
    ServerNonce = TextField(Challenge, "nonce")
    Expected = AuthProof(
        TextField(Record, "token"), "server", ClientNonce, ServerNonce, None
    )
    assert SameProof(TextField(Challenge, "proof"), Expected)
    TokenValue = "0" * 64 if IsWrong else TextField(Record, "token")
    ProofValue = AuthProof(TokenValue, "client", ClientNonce, ServerNonce, RequestValue)
    SendFrame(
        Connection,
        {"proof": ProofValue, "request": RequestValue},
        256 * 1024,
        Deadline,
    )
    return AsRecord(ReadFrame(Connection, 8192, Deadline))
