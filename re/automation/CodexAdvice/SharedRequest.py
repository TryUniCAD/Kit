# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import secrets
import time

from CodexAdvice.SharedBudget import SharedBudget
from Records import canonical, digest


# callers retain their own evidence authority while identical provider prompts share external work
def shared_request(
    call_provider,
    executable,
    packet,
    attempts,
    seconds,
    destination,
    is_current,
    efforts,
    options,
):
    if options.model is None:
        raise ValueError("shared advice requires an explicit model")
    if not 1 <= seconds <= 180:
        raise ValueError("shared advice attempts must take 1 to 180 seconds")
    budget = SharedBudget(
        options.state, options.provider, options.global_calls, options.parallel
    )
    try:
        for effort in efforts:
            if not is_current():
                attempts.append({"effort": effort, "status": "stale"})
                return None
            context = {
                "shared_advice_version": 1,
                "provider": options.provider,
                "auth": options.auth,
                "model": options.model or "cli-default",
                "effort": effort,
                "question": packet["question"],
                "discovery_summary": packet["discovery_summary"],
                "experiments": packet.get("experiments", []),
                "prior_status": attempts[-1]["status"] if attempts else None,
            }
            if len(canonical(context).encode("utf-8")) > 8192:
                raise ValueError("shared advice context exceeds 8 KiB")
            key, token = digest(context), secrets.token_hex(32)
            deadline = time.monotonic() + seconds
            try:
                while True:
                    if not is_current():
                        attempts.append({"effort": effort, "status": "stale"})
                        return None
                    decision = budget.reserve(key, token, seconds)
                    status = decision["status"]
                    if status != "waiting":
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        attempts.append(
                            {
                                "effort": effort,
                                "status": "shared_wait_timeout",
                                "request_key": key,
                            }
                        )
                        return None
                    time.sleep(min(0.2, remaining))
                if status == "cached":
                    attempts.append(
                        {
                            "effort": effort,
                            "status": "shared_proposal",
                            "request_key": key,
                        }
                    )
                    return decision["proposal"] if is_current() else None
                if status != "reserved":
                    attempts.append(
                        {
                            "effort": effort,
                            "status": "shared_" + status,
                            "request_key": key,
                        }
                    )
                    return None
                before = len(attempts)
                try:
                    proposal = call_provider(
                        executable,
                        packet,
                        attempts,
                        seconds,
                        destination,
                        is_current,
                        (effort,),
                        options,
                    )
                except BaseException:
                    budget.finish(key, token, None, attempts[before:], uncertain=True)
                    raise
                uncertain = proposal is None and any(
                    attempt.get("status")
                    in {"timeout", "provider_failed", "launch_failed"}
                    for attempt in attempts[before:]
                )
                budget.finish(
                    key, token, proposal, attempts[before:], uncertain=uncertain
                )
                if uncertain:
                    attempts.append(
                        {
                            "effort": effort,
                            "status": "shared_uncertain",
                            "request_key": key,
                        }
                    )
                    return None
                if proposal is not None:
                    return proposal if is_current() else None
            finally:
                budget.leave(token)
        return None
    finally:
        budget.close()
