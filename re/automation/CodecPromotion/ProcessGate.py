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
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))
from InferenceArchiveGate import GateStore
from InferenceHoldoutGate import HOLDOUT_LINEAGE, SCOPE, submit


def exercise(work, store, statuses, mode, image):
    repo = work / mode
    subprocess.run(["git", "-C", str(ROOT), "worktree", "add", "--detach", "--no-checkout", str(repo), "HEAD"], check=True)

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    git("sparse-checkout", "set", "--no-cone", "/src/", "/Cli/", "/tools/Donors/", "/pyproject.toml", "/Documentation/Changes/Research/", "/tests/Research/CodecPromotion/", "/re/automation/*.py",
        "/re/automation/CodecPromotion/", "/re/Fusion/LocalOracle/PublicAdapter/", "/re/Playbook/README.md")
    git("checkout", "--detach", "HEAD")
    module = f"src/convert/adapters/json/{mode.title()}.py"
    path = repo / module
    original = path.read_text()
    needle = "Document = CadDocument.from_json" if mode == "reader" else "Payload = (DocValue.to_json"
    assert original.count("        " + needle) == 1
    path.write_text(original.replace("        " + needle, '        raise ValueError("seeded process control")\n        ' + needle))
    git("add", module)
    git("-c", "user.name=Process Control", "-c", "user.email=control@example.invalid", "commit", "-qm", "Seed public CLI regression")
    cases = []
    shapes = (("circle", "CircleGeometry"), ("rectangle", "PointGeometry")) if mode == "reader" else (("rectangle", "PointGeometry"), ("cuboid", "PointGeometry"))
    for shape, geometry in shapes:
        sample = f"re/Fusion/LocalOracle/PublicAdapter/{shape}.authoring.json"
        if mode == "writer":
            from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
            from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
            sample = f"re/Fusion/LocalOracle/PublicAdapter/{shape}.control.f3d"
            (repo / sample).write_bytes(EmitDocument(DocumentSpec(shape, "height", 17.0, ProfileKind=shape, ConstrainRectangle=True)))
            git("add", sample)
        cases.append({"file": sample, "sha256": hashlib.sha256((repo / sample).read_bytes()).hexdigest(),
                      "expect": {"/document/sketches/$tuple/0/entities/$tuple/0/geometry/$type": geometry,
                                 "/document/parameters/$tuple/0/value/value": 17.0,
                                 "/document/feature_timeline/$tuple/0/kind/value": "reference"}})
    if mode == "writer":
        git("-c", "user.name=Process Control", "-c", "user.email=control@example.invalid", "commit", "-qm", "Pin dimension-driven native controls")
    name = "Public" + mode.title()
    request = {"name": name, "base": git("rev-parse", "HEAD"), "scope": SCOPE,
               "reference": "re/Playbook/README.md", "rule": "Restore sketch entity geometry for this seeded process control.",
               "modules": [module], "contract": {"mode": mode, "target_suffix": "" if mode == "reader" else ".json", "cases": cases}}
    spec = work / "request.json"
    spec.write_text(json.dumps(request))
    candidate = work / "candidate.json"
    candidate.write_text(json.dumps({module: original}))
    patch = work / (name + ".patch")
    command = [sys.executable, "-m", "KitCli", "research", "--root", str(repo), "codec-patch",
               "--store", str(store), "--request", str(spec), "--image", image, "--output", str(patch),
               "--candidate", str(candidate)]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(map(str, (repo / "src", repo / "Cli")))}
    for case in ("contradiction", "consistent"):
        job = SCOPE + ":" + case
        result = subprocess.run([*command, "--job", job, "--receipt", statuses[job]["receipt"]],
                                capture_output=True, text=True, cwd=repo, env=env)
        if case == "contradiction":
            if result.returncode != 1 or "independent support" not in result.stderr and "refuted inference" not in result.stderr or patch.exists():
                raise RuntimeError("refuted evidence gate: " + result.stderr)
            continue
        if result.returncode:
            raise RuntimeError(result.stderr)
        report = json.loads(result.stdout)
        if (report["passed"], report["baseline_passed"], report["sha256"]) != (2, 0, hashlib.sha256(patch.read_bytes()).hexdigest()):
            raise RuntimeError("invalid qualification receipt")
    git("apply", "--index", "--check", str(patch))
    git("apply", "--index", str(patch))
    subprocess.run([sys.executable, "-m", "pytest", "-q", f"tests/Research/CodecPromotion/{name}Tests.py"],
                   cwd=repo, env=env, check=True)
    print(f"{mode}: baseline 0/2, candidate 2/2, patch applied and regression replayed", flush=True)


if __name__ == "__main__":
    with TemporaryDirectory() as tmp:
        work = Path(tmp)
        gate = GateStore(work)
        submit(gate, "consistent", HOLDOUT_LINEAGE, 7.0)
        submit(gate, "contradiction", HOLDOUT_LINEAGE, 9.0)
        results = gate.run()
        for mode in ("reader", "writer"):
            exercise(work, gate.store, results, mode, sys.argv[1])
