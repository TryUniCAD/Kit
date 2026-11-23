# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Read public CLI observations from one case; expectations stay with the caller."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def run_cli(args, env=None):
    result = subprocess.run(args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return None
    if result.returncode == 1:
        try:
            diagnostic = json.loads(result.stderr)
        except (UnicodeError, ValueError):
            diagnostic = {}
        if diagnostic.get("error") in {"ValueError", "UsabilityError", "RegistryError", "NotImplementedError"}:
            return {"refusal": diagnostic["error"]}
    raise RuntimeError("CLI or qualification environment failed")


def probe(source, mode, suffix, pointers):
    with TemporaryDirectory() as directory:
        output = Path(directory)
        command = [sys.executable, "-c", "from KitCli.MainEntry import MainEntry; raise SystemExit(MainEntry())"]
        if mode == "writer":
            target = output / ("converted" + suffix)
            refusal = run_cli([*command, "convert", str(source), str(target)])
            if refusal:
                return refusal
            source = target
        env = os.environ.copy()
        if mode == "writer" and "KIT_CODEC_REFERENCE" in env:
            root = Path(env["KIT_CODEC_REFERENCE"])
            env["PYTHONPATH"] = os.pathsep.join(map(str, (root / "src", root / "Cli")))
        report = output / "decoded.json"
        refusal = run_cli([*command, "decode", str(source), "-o", str(report)], env)
        if refusal:
            return refusal
        document = json.loads(report.read_bytes())
        if document.get("kind") != "kit.decode" or document.get("partial") is not False:
            raise ValueError("expected a public full decode")
        values = []
        for pointer in pointers:
            item = document
            try:
                for token in pointer[1:].split("/"):
                    key = token.replace("~1", "/").replace("~0", "~")
                    item = item[int(key) if isinstance(item, list) else key]
            except (KeyError, TypeError, IndexError, ValueError):
                values.append({"present": False})
                continue
            values.append({"present": True, "value": item})
        return values


if __name__ == "__main__":
    print(json.dumps(probe(Path(sys.argv[1]), sys.argv[2], sys.argv[3], json.loads(sys.argv[4])), allow_nan=False))
