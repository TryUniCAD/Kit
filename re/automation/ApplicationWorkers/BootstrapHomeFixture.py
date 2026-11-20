# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
BOOT = ROOT / "re/automation/CaptureTools/Runner/KitCaptureRunner/KitCaptureRunner.py"


def host(folder):
    adsk = ModuleType("adsk")
    core = ModuleType("adsk.core")
    app = SimpleNamespace(
        version="protocol fixture",
        registerCustomEvent=lambda event: SimpleNamespace(add=lambda handler: None),
        unregisterCustomEvent=lambda event: None,
        fireCustomEvent=lambda event, payload: True,
    )
    core.Application = SimpleNamespace(get=lambda: app)
    core.CustomEventHandler = object
    adsk.core = core
    sys.modules.update(adsk=adsk, **{"adsk.core": core})
    runtime = runpy.run_path(str(folder / "KitCaptureRunner.py"))
    runtime["run"]({})
    runtime["stop"]({})
    print(json.dumps({"home": str(runtime["HOME"]), "event": runtime["EVENT_ID"]}))


def exercise(root, variant):
    root.mkdir(exist_ok=True)
    home = root / "PrivateHome"
    home.mkdir(mode=0o700)
    allowed = root / "AllowedRoot"
    allowed.mkdir()
    (home / "config.json").write_text(json.dumps({"allowed_root": str(allowed)}))
    installed = root / "Installed"
    installed.mkdir()
    shutil.copyfile(BOOT, installed / BOOT.name)
    selected = home
    if variant == "linked-home":
        selected = root / "LinkHome"
        selected.symlink_to(home, target_is_directory=True)
    elif variant == "public-home":
        home.chmod(0o755)
    elif variant == "missing-home":
        selected = root / "Absent"
    data = {"version": 1, "home": str(selected)}
    if variant == "extra":
        data["extra"] = True
    if variant == "relative":
        data["home"] = "PrivateHome"
    if variant == "boolean-version":
        data["version"] = True
    sidecar = installed / "KitCaptureRunner.runner.json"
    raw = json.dumps(data).encode()
    if variant == "array":
        raw = json.dumps(list(data.items())).encode()
    if variant == "duplicate":
        raw = (
            b'{"version":1,"version":1,"home":' + json.dumps(str(home)).encode() + b"}"
        )
    sidecar.write_bytes(raw)
    sidecar.chmod(0o600)
    if variant == "public-sidecar":
        sidecar.chmod(0o644)
    if variant == "linked-sidecar":
        saved = installed / "Saved.json"
        sidecar.rename(saved)
        sidecar.symlink_to(saved)
    if variant == "oversize":
        sidecar.write_bytes(b" " * 4097)
    before = {path: path.read_bytes() for path in installed.iterdir() if path.is_file()}
    result = subprocess.run(
        [sys.executable, "-B", __file__, "host", str(installed)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    for path, raw in before.items():
        assert path.read_bytes() == raw
    if variant == "private":
        assert result.returncode == 0, result.stderr
        observed = json.loads(result.stdout)
        assert observed["home"] == str(home)
        assert (
            observed["event"]
            == "KitCaptureRunnerJob-" + hashlib.sha256(os.fsencode(home)).hexdigest()
        )
        assert json.loads((home / "runner.json").read_text())["status"] == "stopped"
        assert (home / "queue").is_dir()
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert not (home / "runner.json").exists()
        assert not (home / "queue").exists()
    print(
        json.dumps({"case": variant, "status": "verified", "native_qualified": False})
    )


if __name__ == "__main__":
    if sys.argv[1] == "host":
        host(Path(sys.argv[2]))
    else:
        exercise(Path(sys.argv[1]), sys.argv[2])
