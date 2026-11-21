# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from socket import create_connection as OpenSocket
from time import monotonic as MonoTime


# waiting behind another peer must not refresh an expired generation deadline or start inference
def RejectQueued(Record: dict, RequestValue: dict) -> None:
    from tests.Research.Inference.BuilderDevelopment.Optimizations.PeerAuth import (
        PeerRequest,
    )

    Address = ("127.0.0.1", Record["port"])
    with OpenSocket(Address, timeout=5) as Blocking:
        Blocking.sendall(b"{")
        with OpenSocket(Address, timeout=5) as Waiting:
            RequestValue = {
                **RequestValue,
                "seconds": 0.1,
                "deadline": MonoTime() + 0.1,
            }
            Reply = PeerRequest(Waiting, Record, RequestValue)
    assert "provider_timeout" in Reply.get("error", ""), Reply
    print(EncodeJson(Reply), flush=True)
