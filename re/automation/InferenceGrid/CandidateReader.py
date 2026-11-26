# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import errno
import json
import os
import shutil
import subprocess
import sys

from InferenceInputs import read_file


def link_private_source(source, target):
    try:
        os.link(source, target)
    except OSError as error:
        if error.errno not in {
            errno.ENOTSUP,
            errno.EPERM,
            errno.EACCES,
            errno.EXDEV,
            errno.EMLINK,
        }:
            raise
        shutil.copy2(source, target)


def decode_candidate(
    root, reader, source, scratch, env, stage_name, output_name, path, updated
):
    base = reader / "src"
    if reader == root:
        base = scratch / "base-src"
        if not base.exists():
            shutil.copytree(
                reader / "src", base, ignore=shutil.ignore_patterns("__pycache__")
            )
    stage = scratch / stage_name
    shutil.copytree(base, stage / "src", copy_function=link_private_source)
    (stage / path).unlink()
    (stage / path).write_text(updated)
    output = stage / output_name
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "KitCli",
            "decode",
            str(source),
            "--from",
            "solidworks.sldprt",
            "-o",
            str(output),
        ],
        cwd=stage,
        env={
            **env,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.pathsep.join(map(str, (stage / "src", root / "Cli"))),
        },
        capture_output=True,
        timeout=180,
    )
    if process.returncode:
        if process.returncode == 1 and process.stderr.lstrip().startswith(b"{"):
            failure = json.loads(process.stderr)
            if (
                failure.get("error")
                in {"ValueError", "UsabilityError", "NotImplementedError"}
                and "message" in failure
            ):
                return None
        process.check_returncode()
    return json.loads(read_file(output, 128 * 1024 * 1024))["document"]
