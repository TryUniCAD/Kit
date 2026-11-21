# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from http.client import HTTPConnection, HTTPException
from json import dumps, loads
from time import monotonic


# an explicit loopback connection avoids proxies when advice is kept on device
def post_local(endpoint, payload, seconds):
    connection = HTTPConnection("127.0.0.1", 11434, timeout=seconds)
    try:
        connection.request(
            "POST", endpoint, dumps(payload), {"Content-Type": "application/json"}
        )
        response = connection.getresponse()
        if response.status != 200:
            raise OSError(f"Ollama returned HTTP {response.status}")
        data = response.read(1024 * 1024 + 1)
    except HTTPException:
        raise OSError("Ollama did not return a complete response") from None
    finally:
        connection.close()
    if len(data) > 1024 * 1024:
        raise ValueError("Ollama response exceeds the advice size limit")
    return loads(data)


# check the installed model metadata before submitting an on device prompt
def call_ollama(options, prompt, schema, seconds):
    started = monotonic()
    model = post_local("/api/show", {"model": options.model}, seconds)
    if (
        not isinstance(model, dict)
        or not model.get("model_info")
        or any(model.get(key) for key in ("remote_host", "remote_model"))
    ):
        raise ValueError("Ollama did not identify an installed local model")
    remaining = seconds - (monotonic() - started)
    if remaining <= 0:
        raise TimeoutError
    response = post_local(
        "/api/chat",
        {
            "model": options.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": schema,
            "options": {"num_predict": 1024},
        },
        remaining,
    )
    try:
        return loads(response["message"]["content"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Ollama did not return a structured proposal") from None
