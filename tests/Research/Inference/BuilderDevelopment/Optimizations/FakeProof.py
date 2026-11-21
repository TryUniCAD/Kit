# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import urandom as RandomBytes
from time import monotonic as MonoTime


# an unrelated endpoint cannot learn the generation prompt before proving possession of the broker secret
def SendBadProof(Listener) -> dict:
    from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire import (
        ReadFrame,
        SendFrame,
    )

    Connection, Address = Listener.accept()
    with Connection:
        FirstFrame = ReadFrame(Connection, 256 * 1024, MonoTime() + 5)
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
