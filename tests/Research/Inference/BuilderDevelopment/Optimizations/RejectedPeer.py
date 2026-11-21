# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from socket import create_connection as OpenSocket
from time import monotonic as MonoTime


# malformed authenticated peers cross the actual bounded socket parser before receiving rejection
def RejectPeer(Record: dict, RequestValue: dict, ModeName: str) -> dict:
    from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire import ReadFrame
    from tests.Research.Inference.BuilderDevelopment.Optimizations.PeerAuth import (
        PeerRequest,
    )

    with OpenSocket(("127.0.0.1", Record["port"]), timeout=5) as Connection:
        if ModeName == "oversized":
            Connection.sendall(b"x" * (300 * 1024) + b"\n")
        elif ModeName == "incomplete":
            Connection.sendall(b"{")
        else:
            return PeerRequest(Connection, Record, RequestValue, ModeName == "token")
        try:
            return ReadFrame(Connection, 8192, MonoTime() + 8)
        except OSError as Error:
            return {"error": "provider_unavailable: " + str(Error)}
