# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hmac import compare_digest as SameProof
from os import urandom as RandomBytes
from time import monotonic as MonoTime


# authenticated fixture peers prove broker rejection without placing its private token on the wire
def PeerRequest(
    Connection, Record: dict, RequestValue: dict, IsWrong: bool = False
) -> dict:
    from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerAuth import AuthProof
    from InferenceGrid.BuilderDevelopment.Generation.Broker.BrokerWire import (
        ReadFrame,
        SendFrame,
    )

    ClientNonce = RandomBytes(32).hex()
    Deadline = MonoTime() + 8
    SendFrame(Connection, {"hello": ClientNonce}, 8192, Deadline)
    Challenge = ReadFrame(Connection, 8192, Deadline)
    ServerNonce = Challenge["nonce"]
    Expected = AuthProof(Record["token"], "server", ClientNonce, ServerNonce)
    assert SameProof(Challenge["proof"], Expected)
    TokenValue = "0" * 64 if IsWrong else Record["token"]
    ProofValue = AuthProof(TokenValue, "client", ClientNonce, ServerNonce, RequestValue)
    SendFrame(
        Connection,
        {"proof": ProofValue, "request": RequestValue},
        256 * 1024,
        Deadline,
    )
    return ReadFrame(Connection, 8192, Deadline)
