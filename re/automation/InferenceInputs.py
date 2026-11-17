# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import math
import os
import re
import stat

from Records import label

PLAN_FIELDS = {
    "inference_version",
    "scope",
    "quantity",
    "provenance",
    "encodings",
    "tolerance",
    "confounds",
    "observations",
}
OBSERVATION_FIELDS = {
    "id",
    "lineage",
    "sha256",
    "stream",
    "start",
    "length",
    "value",
    "controls",
    "role",
    "split",
}
SPLITS = ("discovery", "holdout", "challenge")
STREAM_LIMIT = 16 * 1024 * 1024
INPUT_BUDGET = 64 * 1024 * 1024


def checksum(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("an inference input must have a lowercase SHA-256")
    return value


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_file(path, limit):
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or getattr(before, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        or before.st_size > limit
    ):
        raise ValueError("inference input must be a bounded plain regular file")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
    )
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
        ) != (
            before.st_dev,
            before.st_ino,
            before.st_size,
        ):
            raise ValueError("inference input identity changed before reading")
        content = source.read(limit + 1)
        after = os.fstat(source.fileno())
    current = path.lstat()
    if (
        len(content) != before.st_size
        or len(content) > limit
        or (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        != (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
        or (
            current.st_dev,
            current.st_ino,
            current.st_size,
            current.st_mtime_ns,
            current.st_ctime_ns,
        )
        != (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
    ):
        raise ValueError("inference input changed while reading")
    return content


def unique_object(pairs):
    value = dict(pairs)
    if len(value) != len(pairs):
        raise ValueError("inference metadata contains duplicate keys")
    return value


def parse_metadata(content):
    try:
        value = json.loads(content, object_pairs_hook=unique_object)
        if not isinstance(value, dict):
            raise ValueError("inference metadata must be an object")
        pending = [(value, 0)]
        visited = 0
        while pending:
            item, depth = pending.pop()
            visited += 1
            if depth > 64 or visited + len(pending) > 200000:
                raise ValueError("inference metadata exceeds its structural limit")
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
            elif isinstance(item, float) and not math.isfinite(item):
                raise ValueError("inference metadata contains a nonfinite number")
        return value
    except RecursionError as error:
        raise ValueError("inference metadata exceeds its structural limit") from error


def read_input(session, descriptor, limit):
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "binding",
        "sha256",
        "path",
    }:
        raise ValueError("inference input requires the version 1 session descriptor")
    expected = checksum(descriptor["sha256"])
    relative = f"inputs/{expected}"
    path = session / relative
    if descriptor["path"] != relative or path.resolve() != path:
        raise ValueError("inference input escaped its content-addressed session path")
    content = read_file(path, limit)
    if sha256(content) != expected:
        raise ValueError("inference input exceeded its limit or differed from its pin")
    return content


def read_json_input(session, descriptor):
    return parse_metadata(read_input(session, descriptor, 1024 * 1024))


def observations(plan):
    if (
        not isinstance(plan, dict)
        or set(plan) != PLAN_FIELDS
        or type(plan["inference_version"]) is not int
        or plan["inference_version"] != 1
        or not isinstance(plan["provenance"], dict)
        or not plan["provenance"]
    ):
        raise ValueError("inference plan does not match version 1")
    label(plan["scope"])
    label(plan["quantity"])
    rows = plan["observations"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 63:
        raise ValueError("inference plan must have 1–63 observations")
    identities = set()
    provenance_inputs = plan["provenance"].get("inputs")
    if not isinstance(provenance_inputs, dict):
        raise ValueError("inference plan must pin the source streams")
    for observation in rows:
        if not isinstance(observation, dict) or set(observation) != OBSERVATION_FIELDS:
            raise ValueError("invalid inference observation record")
        identity = label(observation["id"])
        label(observation["lineage"])
        checksum(observation["sha256"])
        if (
            identity in identities
            or label(observation["role"]) == "plan"
            or observation["split"] not in SPLITS
        ):
            raise ValueError("invalid inference observation identity, role, or split")
        provenance = provenance_inputs.get(identity)
        if not isinstance(provenance, dict):
            raise ValueError("inference observation lacks source provenance")
        if provenance.get("archive_sha256") != observation["sha256"]:
            raise ValueError(
                "inference observation differs from its source archive pin"
            )
        checksum(provenance["stream_sha256"])
        identities.add(identity)
    if set(provenance_inputs) != identities:
        raise ValueError(
            "inference stream provenance does not match the observation roster"
        )
    return rows


def read_plan(session, descriptors, scope):
    plan_pin = descriptors["plan"]
    plan = read_json_input(session, plan_pin)
    rows = observations(plan)
    roles = {observation["role"] for observation in rows}
    if set(descriptors) != roles | {"plan"} or plan["scope"] != scope:
        raise ValueError(
            "inference inputs do not match the planned scope and stream roles"
        )
    for observation in rows:
        provenance = plan["provenance"]["inputs"][observation["id"]]
        if provenance["stream_sha256"] != descriptors[observation["role"]]["sha256"]:
            raise ValueError("inference stream differs from its observation pin")
    streams = {}
    contents = {}
    budget = INPUT_BUDGET
    for role in sorted(roles):
        descriptor = descriptors[role]
        pin = checksum(descriptor["sha256"])
        if pin not in contents:
            content = read_input(session, descriptor, min(STREAM_LIMIT, budget))
            budget -= len(content)
            contents[pin] = content
        elif descriptor["path"] != f"inputs/{pin}":
            raise ValueError("reused stream does not name its content address")
        streams[role] = contents[pin]
    return plan, streams, plan_pin["sha256"]
