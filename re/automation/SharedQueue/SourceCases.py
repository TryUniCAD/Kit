# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# native lifecycle admission must detect changes in its new transitive queue policy
SHARED_POLICY = (
    "Commands.py",
    "Lifecycle.py",
    "Plan.py",
    "Ranking.py",
    "Report.py",
    "State.py",
    "Stats.py",
    "Dispatch.py",
    "Demand.py",
    "Submit.py",
)


# probe processes use the fixture checkout without replacing any production validation function
def probe(root, revision):
    automation = root / "re/automation"
    sys.path.insert(0, str(automation))
    sys.path.insert(0, str(automation / "ApplicationWorkers"))
    from FusionLifecycleRegistration import checked_policy

    config = {
        "application": "fusion",
        "installation": "fusion:source-fixture",
        "macos_automatic_quit": True,
        "source_root": str(root),
        "source_revision": revision,
    }
    try:
        result = checked_policy(config, "application:fusion:source-fixture")
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "refused", "error": str(error)}))
        return 1
    print(json.dumps({"status": "accepted", "installation_sha256": result}))
    return 0


# an explicit import closure avoids copying unrelated research and native fixtures
def import_closure(root, paths):
    automation = root / "re/automation"
    search = (automation, automation / "ApplicationWorkers")
    pending, selected = list(paths), set()
    while pending:
        path = pending.pop()
        if path in selected:
            continue
        selected.add(path)
        body = list(ast.parse(path.read_text(encoding="utf-8")).body)
        while body:
            statement = body.pop()
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue
            if isinstance(statement, ast.Import):
                names = [item.name for item in statement.names]
            elif isinstance(statement, ast.ImportFrom) and statement.level == 0:
                names = [statement.module] if statement.module else []
            else:
                body.extend(ast.iter_child_nodes(statement))
                continue
            for name in names:
                for base in search:
                    candidate = base.joinpath(*name.split(".")).with_suffix(".py")
                    if candidate.is_file():
                        pending.append(candidate)
                        break
    return selected


# subprocess diagnostics remain available when the source custody boundary regresses
def invoke(arguments, root=None):
    result = subprocess.run(
        arguments,
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=60,
        env={
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        },
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout.strip()


# immutable fixture commits let clean and drifted checkouts exercise real git object comparisons
def source_fences():
    source = Path(__file__).resolve().parents[3]
    if sys.platform != "darwin":
        revision = invoke(["git", "rev-parse", "HEAD"], source)
        command = [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--probe",
            str(source),
            "--revision",
            revision,
        ]
        result = subprocess.run(
            command, capture_output=True, encoding="utf-8", check=False, timeout=60
        )
        if (
            result.returncode != 1
            or "same pinned macOS owner controller and installation"
            not in result.stdout
        ):
            raise AssertionError(
                "non native host did not refuse automatic lifecycle policy"
            )
        return {
            "status": "passed",
            "scenario": "source-fences",
            "scope": "platform-refusal",
            "checked_members": 0,
            "missing_member_refused": False,
            "native_application_started": False,
        }
    policy = source / "re/automation/ApplicationWorkers/FusionLifecycleRegistration.py"
    tree = ast.parse(policy.read_text(encoding="utf-8"))
    names = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "POLICY_FILES"
            for target in node.targets
        )
    )
    for member in SHARED_POLICY:
        if "SharedQueue/" + member not in names:
            raise AssertionError(
                "shared policy dependency is absent from the reviewed source inventory"
            )
    paths = import_closure(source, [source / "re/automation" / name for name in names])
    with tempfile.TemporaryDirectory(prefix="kit-source-fence-") as temporary:
        root = Path(temporary).resolve()
        for path in paths:
            target = root / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        invoke(["git", "init", "--initial-branch", "source-proof"], root)
        invoke(["git", "add", "--", "re"], root)
        invoke(
            [
                "git",
                "-c",
                "user.name=Kit Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Test - Pin source custody fixture",
            ],
            root,
        )
        revision = invoke(["git", "rev-parse", "HEAD"], root)
        command = [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--probe",
            str(root),
            "--revision",
            revision,
        ]
        baseline = json.loads(invoke(command))
        if baseline["status"] != "accepted":
            raise AssertionError("clean reviewed policy was not accepted")
        for member in SHARED_POLICY:
            path = root / "re/automation/SharedQueue" / member
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    encoding="utf-8",
                    check=False,
                    timeout=60,
                )
                if (
                    result.returncode != 1
                    or "reviewed controller and supervisor source policy"
                    not in result.stdout
                ):
                    raise AssertionError(
                        f"changed shared policy was not refused: {member}: {result.stdout}{result.stderr}"
                    )
            finally:
                path.write_bytes(original)
        missing = root / "re/automation/SharedQueue/Report.py"
        original = missing.read_bytes()
        missing.unlink()
        try:
            result = subprocess.run(
                command, capture_output=True, encoding="utf-8", check=False, timeout=60
            )
            if result.returncode != 1:
                raise AssertionError("missing reviewed shared policy was not refused")
        finally:
            missing.write_bytes(original)
        if json.loads(invoke(command)) != baseline:
            raise AssertionError(
                "restored source custody differs from the original accepted pin"
            )
    return {
        "status": "passed",
        "scenario": "source-fences",
        "scope": "native-source-policy",
        "checked_members": len(SHARED_POLICY),
        "copied_sources": len(paths),
        "missing_member_refused": True,
        "native_application_started": False,
    }


# maintained source checks run through a real isolated policy and git process boundary
def main():
    parser = argparse.ArgumentParser(
        description="Verify new shared queue modules are bound by native lifecycle source custody"
    )
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    if args.probe is not None:
        if args.revision is None:
            parser.error("--probe requires --revision")
        return probe(args.probe.resolve(), args.revision)
    print(json.dumps(source_fences()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
