# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
import subprocess
from threading import Timer
from uuid import uuid4

from CodecPromotion.Contract import matches


def observe(tree, sample, contract, case, image, reference):
    name = "kit-codec-" + uuid4().hex
    probe = Path(__file__).with_name("Probe.py").resolve()
    source = "/input" + sample.suffix
    argv = [
        "docker", "run", "--rm", "--pull=never", "--name", name, "--network=none",
        "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--user=65534:65534", "--pids-limit=64", "--memory=1g", "--cpus=1",
        "--log-driver=none", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=256m,mode=1777",
        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONPATH=/kit/src:/kit/Cli",
        "--volume", f"{reference}:/reference:ro", "--env", "KIT_CODEC_REFERENCE=/reference",
        "--volume", f"{tree}:/kit:ro", "--volume", f"{sample}:{source}:ro",
        "--volume", f"{probe}:/probe.py:ro", "--entrypoint", "python", image,
        "/probe.py", source, contract["mode"], contract["target_suffix"], json.dumps(list(case["expect"])),
    ]
    with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        timer = Timer(120, process.kill)
        timer.start()
        try:
            output = process.stdout.read(65537)
            if len(output) > 65536:
                raise ValueError("qualification response exceeds 64 KiB")
            if process.wait(timeout=120):
                raise ValueError("qualification container failed")
        finally:
            timer.cancel()
            process.kill()
            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    return matches(json.loads(output), case["expect"].values())
