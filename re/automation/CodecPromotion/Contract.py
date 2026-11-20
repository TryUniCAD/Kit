# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import math
from pathlib import PurePosixPath
import re


def relative(path):
    if not isinstance(path, str) or len(path) > 300 or not re.fullmatch(r"[A-Za-z0-9_./ -]+", path):
        raise ValueError("invalid repository path")
    parts = PurePosixPath(path).parts
    if not parts or any(part.startswith(".") for part in parts) or str(PurePosixPath(path)) != path or path.startswith("/"):
        raise ValueError("expected a normalized relative path")
    return path


def validate(contract, discovery):
    if set(contract) != {"mode", "target_suffix", "cases"} or contract["mode"] not in ("reader", "writer"):
        raise ValueError("invalid qualification contract")
    if contract["mode"] == "writer":
        if not re.fullmatch(r"\.[A-Za-z0-9]{1,12}", contract["target_suffix"]):
            raise ValueError("writer requires a destination extension")
    elif contract["target_suffix"] != "":
        raise ValueError("reader requires an empty target suffix")
    cases = contract["cases"]
    if not isinstance(cases, list) or not 2 <= len(cases) <= 16:
        raise ValueError("require two to sixteen independent qualification cases")
    pins = set(discovery)
    for case in cases:
        if set(case) != {"file", "sha256", "expect"} or not relative(case["file"]).startswith(("re/", "examples/", "tests/")):
            raise ValueError("expected a tracked qualification sample")
        pin = case["sha256"]
        if not re.fullmatch("[a-f0-9]{64}", pin) or pin in pins:
            raise ValueError("qualification samples must be distinct from discovery and each other")
        pins.add(pin)
        checks = case["expect"]
        if not isinstance(checks, dict) or not 1 <= len(checks) <= 32:
            raise ValueError("expected independent semantic measurements")
        for path, value in checks.items():
            if not path.startswith("/document/") or len(path) > 512 or not isinstance(value, (str, int, float, bool)) or isinstance(value, float) and not math.isfinite(value):
                raise ValueError("expected a document pointer and a finite scalar measurement")


def matches(values, expected):
    return isinstance(values, list) and len(values) == len(expected) and all(
        isinstance(value, dict) and "value" in value and value.get("present") is True and (
            math.isclose(value["value"], target, rel_tol=1e-9, abs_tol=1e-9)
            if type(target) is float and type(value["value"]) in (float, int)
            else type(value["value"]) is type(target) and value["value"] == target
        ) for value, target in zip(values, expected, strict=True)
    )


def verify_file(path, pin):
    with path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != pin:
            raise ValueError("qualification sample hash differs")
