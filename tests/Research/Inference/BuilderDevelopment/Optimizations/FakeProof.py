# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from os import urandom as RandomBytes
from socket import socket as SocketType
from typing import cast as TypeCast
from time import monotonic as MonoTime

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    AsRecord,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# an unrelated endpoint cannot learn the generation prompt before proving possession of the broker secret
def SendBadProof(Listener: SocketType) -> dict[str, object]:
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

    Connection, Address = Listener.accept()
    with Connection:
        FirstFrame = AsRecord(ReadFrame(Connection, 256 * 1024, MonoTime() + 5))
        SendFrame(
            Connection,
            {"nonce": RandomBytes(32).hex(), "proof": "0" * 64},
            8192,
            MonoTime() + 3,
        )
        Connection.settimeout(3)
        ExtraBytes = Connection.recv(65536)
    return {
        "frames": [FirstFrame],
        "extra_bytes": len(ExtraBytes),
        "closed_before_request": not ExtraBytes,
        "peer_host": Address[0],
    }
