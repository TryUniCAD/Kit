# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from hmac import new as NewHmac
from json import dumps


# mutual proofs prevent a reused local port from receiving the private token or model prompt
def AuthProof(Token, Role, ClientNonce, ServerNonce, Request=None):
    for Value in (Token, ClientNonce, ServerNonce):
        if not isinstance(Value, str) or len(Value) != 64:
            raise ValueError(
                "provider_unavailable: invalid local broker authentication value"
            )
        try:
            if len(bytes.fromhex(Value)) != 32:
                raise ValueError("invalid length")
        except ValueError as Error:
            raise ValueError(
                "provider_unavailable: invalid local broker authentication value"
            ) from Error
    Raw = dumps(
        {
            "role": Role,
            "client": ClientNonce,
            "server": ServerNonce,
            "request": Request,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return NewHmac(bytes.fromhex(Token), Raw, sha256).hexdigest()
