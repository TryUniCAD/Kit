# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


import math
import sys

from InferenceSession import check_session, read_packet


def group_members(session, kind):
    single = session / "job.json"
    if single.exists() or single.is_symlink():
        raise ValueError(
            "inference session cannot contain both group and job manifests"
        )
    group = read_packet(session / "group.json")
    if (
        set(group) != {"group_session_version", "session", "pool", "members", "stop_at"}
        or type(group["group_session_version"]) is not int
        or group["group_session_version"] != 1
        or group["session"] != session.name
        or not isinstance(group["pool"], str)
        or not group["pool"]
        or type(group["stop_at"]) not in (int, float)
        or not math.isfinite(group["stop_at"])
    ):
        raise ValueError("inference group does not match protocol 1")
    names = group["members"]
    if (
        not isinstance(names, list)
        or not 2 <= len(names) <= 20
        or names != [f"jobs/{index:02d}/job.json" for index in range(len(names))]
    ):
        raise ValueError("inference group requires 2–20 ordered private members")

    members, identities, versions = [], set(), set()
    for name in names:
        path = session / name
        if path.resolve() != path:
            raise ValueError("inference group member path is aliased")
        packet = read_packet(path)
        job = packet["job"]
        if (
            packet["session"] != group["session"]
            or packet["pool"] != group["pool"]
            or packet["stop_at"] != group["stop_at"]
            or job["kind"] != kind
            or job["id"] in identities
        ):
            raise ValueError(
                "inference group membership differs from its private claims"
            )
        identities.add(job["id"])
        versions.add((job["rule_version"], job["tool_version"]))
        members.append((path.parent, packet))
    if len(versions) != 1:
        raise ValueError("inference rescan groups must share rule and tool revisions")
    return members


def run_rescans(session, kind, worker):
    for directory, packet in group_members(session, kind):
        try:
            worker(directory, *check_session(packet))
        except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as error:
            sys.stderr.write(
                f"{directory.name}: inference rescan refused: {str(error)[:512]}\n"
            )
