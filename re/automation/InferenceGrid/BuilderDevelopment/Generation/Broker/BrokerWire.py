# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps, loads
from time import monotonic


# bounded local frames keep a malformed peer from holding the provider indefinitely
def ReadFrame(Connection, Limit, Deadline):
    Buffer = bytearray()
    while b"\n" not in Buffer:
        Remaining = Deadline - monotonic()
        if Remaining <= 0:
            raise TimeoutError("provider_timeout: waiting for the local broker")
        Connection.settimeout(Remaining)
        Chunk = Connection.recv(min(65536, Limit + 1 - len(Buffer)))
        if not Chunk:
            raise OSError("provider_unavailable: local broker closed the connection")
        Buffer.extend(Chunk)
        if len(Buffer) > Limit:
            raise ValueError(
                "provider_output_limit: local broker frame exceeds its bound"
            )
    Line, Extra = bytes(Buffer).split(b"\n", 1)
    if Extra:
        raise ValueError(
            "provider_unavailable: multiple local broker frames are not allowed"
        )
    return loads(Line)


# only json crosses the local transport so receiving a frame never executes peer supplied objects
def SendFrame(Connection, Value, Limit, Deadline):
    Raw = (
        dumps(Value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
        + b"\n"
    )
    if len(Raw) > Limit:
        raise ValueError("provider_output_limit: local broker frame exceeds its bound")
    Remaining = Deadline - monotonic()
    if Remaining <= 0:
        raise TimeoutError("provider_timeout: local broker deadline expired")
    Connection.settimeout(Remaining)
    Connection.sendall(Raw)
