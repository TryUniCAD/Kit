# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from socket import create_connection as OpenSocket, socket as SocketType
from typing import cast as TypeCast
from time import monotonic as MonoTime

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    AsRecord,
    CountField,
    ReadRecord,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# malformed authenticated peers cross the actual bounded socket parser before receiving rejection
def RejectPeer(
    Record: dict[str, object], RequestValue: dict[str, object], ModeName: str
) -> dict[str, object]:
    ReadFrame = TypeCast(
        Callable[[SocketType, int, float], object],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire", "ReadFrame"
        ),
    )
    from tests.Research.Inference.BuilderDevelopment.Optimizations.PeerAuth import (
        PeerRequest,
    )

    with OpenSocket(("127.0.0.1", CountField(Record, "port")), timeout=5) as Connection:
        if ModeName == "oversized":
            Prefix, Suffix = b'{"hello":"', b'"}\n'
            Payload = Prefix + b"x" * (4097 - len(Prefix) - len(Suffix)) + Suffix
            _ = ReadRecord(Payload)
            Connection.sendall(Payload)
        elif ModeName == "incomplete":
            Connection.sendall(b"{")
        else:
            return PeerRequest(Connection, Record, RequestValue, ModeName == "token")
        try:
            return AsRecord(ReadFrame(Connection, 8192, MonoTime() + 8))
        except OSError as Error:
            return {"error": "provider_unavailable: " + str(Error)}
