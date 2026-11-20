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

# disposable source commits establish authority without using a licensed application
ROOT = Path(__file__).resolve().parents[3]

# the real bootstrap must load every early helper from its exact committed source
SOURCES = (
    "re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py",
    "re/automation/ApplicationWorkers/ApplicationProtocol.py",
    "re/automation/ApplicationWorkers/WindowsIdentity.py",
    "re/automation/ApplicationWorkers/WindowsRecords.py",
)


# fixture preparation must remain independent from the implementation under test
def git(root, *arguments):
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(root), *arguments],
        env=environment,
        stderr=subprocess.PIPE,
        timeout=30,
    )


# only the application event surface is authored while installed source loading remains real
def host(root, variant):
    fixture = runpy.run_path(str(ROOT / "tests/Research/Windows/FusionStub.py"))
    app = fixture["StubFusion"]()
    adsk = ModuleType("adsk")
    core = ModuleType("adsk.core")
    core.Application = SimpleNamespace(get=lambda: app)
    core.CustomEventHandler = object
    adsk.core = core
    sys.modules.update(adsk=adsk, **{"adsk.core": core})
    inherited = dict(os.environ)
    runner = runpy.run_path(str(root / "Installed/KitCaptureRunner.py"))
    runner["run"]({})
    try:
        protocol = runner["state"]["dispatch_protocol"]
        config = runner["state"]["dispatch"].config
        source = root / "Checkout" / SOURCES[1]
        original = source.read_bytes()
        if variant == "downstream-dirty":
            source.write_bytes(original + b"\n")
        try:
            observed = protocol["committed_bytes"](config, protocol["PROTOCOL"])
            assert observed == original
        finally:
            if variant == "downstream-dirty":
                source.write_bytes(original)
        assert dict(os.environ) == inherited
        print(json.dumps({"source_sha256": hashlib.sha256(observed).hexdigest()}))
    finally:
        runner["stop"]({})
        runner["state"]["thread"].join(timeout=5)


# real installed bootstrap processes must ignore ambient git authority but retain exact source guards
def exercise(root, variant):
    root.mkdir(exist_ok=True)
    checkout = root / "Checkout"
    checkout.mkdir()
    for relative in SOURCES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    git(checkout, "init", "--quiet", "--initial-branch=fixture/git-isolation")
    git(checkout, "add", "--", *SOURCES)
    git(
        checkout,
        "-c",
        "user.name=Bootstrap Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        f"core.hooksPath={os.devnull}",
        "commit",
        "--quiet",
        "-m",
        "Test - Pin bootstrap source",
    )
    revision = git(checkout, "rev-parse", "HEAD").decode().strip()
    endpoint = root / "Endpoint"
    endpoint.mkdir()
    installed = root / "Installed"
    installed.mkdir()
    bootstrap = installed / "KitCaptureRunner.py"
    shutil.copyfile(checkout / SOURCES[0], bootstrap)
    home = root / "AppData/KitCaptureRunner"
    home.mkdir(parents=True)
    config = {
        "version": 1,
        "installation": "fixture:git-isolation",
        "application": "fusion",
        "windows_phase_a": True,
        "endpoint": str(endpoint),
        "source_root": str(checkout),
        "source_revision": revision,
    }
    if variant == "installation-root":
        config["source_root"] = str(root)
    if variant == "no-opt-in":
        del config["windows_phase_a"]
    installation = root / "Installation.json"
    installation.write_text(json.dumps(config))
    (home / "config.json").write_text(
        json.dumps(
            {
                "allowed_root": str(checkout / "re/automation/PairedCaptures"),
                "dispatch": str(installation),
            }
        )
    )
    if variant == "dirty-protocol":
        with (checkout / SOURCES[1]).open("ab") as stream:
            stream.write(b"\n")
    if variant == "installed-mismatch":
        with bootstrap.open("ab") as stream:
            stream.write(b"\n")
    malformed = root / "MalformedGitConfig"
    malformed.write_text("[invalid configuration\n")
    environment = dict(os.environ, APPDATA=str(home.parent))
    overrides = {
        "git-directory": {"GIT_DIR": str(root / "AbsentGit")},
        "git-worktree": {"GIT_WORK_TREE": str(root)},
        "git-objects": {"GIT_OBJECT_DIRECTORY": str(root / "AbsentObjects")},
        "git-config": {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.bare",
            "GIT_CONFIG_VALUE_0": "true",
        },
        "git-global": {"GIT_CONFIG_GLOBAL": str(malformed)},
        "git-system": {"GIT_CONFIG_SYSTEM": str(malformed), "GIT_CONFIG_NOSYSTEM": "0"},
        "git-grafts": {"GIT_GRAFT_FILE": str(root / "AbsentGrafts")},
        "git-replacements": {"GIT_REPLACE_REF_BASE": "refs/untrusted/"},
    }
    environment.update(overrides.get(variant, {}))
    before = {relative: (checkout / relative).read_bytes() for relative in SOURCES}
    result = subprocess.run(
        [sys.executable, "-I", "-S", __file__, "host", str(root), variant],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    reasons = {
        "dirty-protocol": "application source differs from its pinned revision",
        "installed-mismatch": "reload the add-in from the trusted installation revision",
        "installation-root": "dispatch installation must pin this configured repository",
        "no-opt-in": "Windows Fusion Phase A requires owner opt-in",
        "downstream-dirty": "application input differs from the installed trusted revision",
    }
    if variant in reasons:
        assert (
            result.returncode != 0 and reasons[variant] in result.stderr
        ), result.stderr
        if variant != "downstream-dirty":
            assert not (home / "runner.json").exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout) == {
            "source_sha256": hashlib.sha256(before[SOURCES[1]]).hexdigest()
        }
    assert all(
        (checkout / relative).read_bytes() == raw for relative, raw in before.items()
    )
    assert not (home / "queue").exists()
    print(
        json.dumps({"case": variant, "status": "verified", "native_qualified": False})
    )


if __name__ == "__main__":
    if sys.argv[1] == "host":
        host(Path(sys.argv[2]), sys.argv[3])
    else:
        exercise(Path(sys.argv[1]), sys.argv[2])
