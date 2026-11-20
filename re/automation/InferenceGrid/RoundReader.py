# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from InferenceGrid.RoundSurface import closed_surface
from InferenceInputs import read_file


def reader_source(shape):
    if shape == "Sphere":
        geometry = """    r = surface.RadiusCm * scale
    radii = {"radiusCm": r}
    widths = (r, r, r)
    volume = 4 * pi * r**3 / 3
    area = 4 * pi * r**2"""
    else:
        geometry = """    major = surface.MajorRadiusCm * scale
    minor = surface.MinorRadiusCm * scale
    if not major > minor > 0:
        raise ValueError("expected a ring torus")
    radii = {"majorRadiusCm": major, "minorRadiusCm": minor, "axis": axis}
    widths = [minor + major * sqrt(max(0.0, 1 - v*v)) for v in axis]
    volume = 2 * pi**2 * major * minor**2
    area = 4 * pi**2 * major * minor"""
    return f"""from math import pi{", sqrt" if shape == "Torus" else ""}
from pathlib import Path
import json
import sys

from convert.Formats.Fusion.BrepCodec.Journal.Round.{shape}Node import {shape}Node
from InferenceGrid.RoundSurface import closed_surface
from InferenceInputs import read_file


def read(data):
    surface, center, axis, scale = closed_surface(data)
    if not isinstance(surface, {shape}Node):
        raise ValueError("expected a {shape.lower()} surface")
{geometry}
    return {{**radii, "centerCm": center, "volumeCm3": volume, "areaCm2": area,
            "boundsCm": [[v-w for v,w in zip(center,widths)], [v+w for v,w in zip(center,widths)]],
            "faces": 1, "edges": 0, "vertices": 0}}


if __name__ == "__main__":
    print(json.dumps(read(read_file(Path(sys.argv[1]), 32 * 1024 * 1024)), allow_nan=False))
"""


def matches(observed, predicted):
    if not isinstance(observed, dict) or observed.get("solid") is not True:
        return False

    def equal(left, right):
        if isinstance(right, list):
            return (
                isinstance(left, list)
                and len(left) == len(right)
                and all(equal(a, b) for a, b in zip(left, right))
            )
        return type(left) in (int, float) and math.isclose(
            left, right, rel_tol=1e-8, abs_tol=1e-8
        )

    return all(
        equal(observed.get(k), predicted[k])
        for k in (
            "faces",
            "edges",
            "vertices",
            "centerCm",
            "boundsCm",
            "areaCm2",
            "volumeCm3",
        )
    )


def round_reader(root, data, pin, scratch):
    try:
        surface = closed_surface(data)[0]
    except ValueError as error:
        return None, str(error)[:250], None
    shape = "Sphere" if isinstance(surface, SphereNode) else "Torus"
    relative = "re/Fusion/Reconstruction/AnalyticReaders/" + shape + "Reader.py"
    code = reader_source(shape)
    program = scratch / (shape + "Reader.py")
    program.write_text(code, encoding="utf-8")
    snapshot = scratch / "model.smb"
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(map(str, (root / "src", root / "re/automation"))),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    def replay(raw):
        snapshot.write_bytes(raw)
        process = subprocess.run(
            [sys.executable, str(program), str(snapshot)],
            cwd=scratch,
            env=env,
            capture_output=True,
            timeout=60,
            check=True,
        )
        return json.loads(process.stdout)

    try:
        predicted = replay(data)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return (
            None,
            "generated reader refused the input or exceeded its replay budget",
            None,
        )
    folder = root / "re/Fusion/LocalOracle/RoundBodies"
    receipt = folder / "NativeAcceptance.json"
    report = {
        "status": "decoded_profile",
        "profile": shape,
        "model": predicted,
        "replays": [],
        "reader_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "native_witness": None,
    }
    if not receipt.is_file():
        return report, None, None
    raw = read_file(receipt, 4 * 1024 * 1024)
    native = json.loads(raw)
    cases = {
        row[key]: row
        for group, key in (
            ("standalone", "source_sha256"),
            ("geometry", "target_sha256"),
        )
        for row in native[group]
        if row["status"] == "accepted"
    }
    wanted = {
        digest
        for digest, row in cases.items()
        if row["reopened"].get("surfaceTypes") == ["adsk::core::" + shape]
    }
    seen = set()
    for path in [None, *sorted(folder.glob("*.smb"))]:
        content = data if path is None else read_file(path, 32 * 1024 * 1024)
        digest = hashlib.sha256(content).hexdigest()
        if digest not in wanted or digest in seen:
            continue
        seen.add(digest)
        case = cases[digest]
        try:
            result = predicted if digest == pin else replay(content)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            report["replays"].append(
                {
                    "source_sha256": digest,
                    "geometry_matches": False,
                    "status": "reader_replay_failed",
                }
            )
            continue
        ok = matches(case["reopened"], result)
        witness = {
            "source_sha256": digest,
            "saved_document_sha256": case["saved_sha256"],
            "observations_sha256": hashlib.sha256(raw).hexdigest(),
            "stage": "reopened",
            "geometry_matches": ok,
            "predicted": result,
            "observed": case["reopened"],
        }
        report["replays"].append(witness)
        if digest == pin:
            report["native_witness"] = witness
    replays = report["replays"]
    report["missing_control_sha256"] = sorted(wanted - seen)
    if (
        wanted != seen
        or not all(row["geometry_matches"] for row in replays)
        or len({row["predicted"]["volumeCm3"] for row in replays}) < 2
        or (root / relative).exists()
    ):
        return report, None, None
    patch = "".join(
        difflib.unified_diff([], code.splitlines(True), "/dev/null", "b/" + relative)
    )
    return (
        report,
        None,
        {
            "patch": patch,
            "path": relative,
            "input_sha256": pin,
            "target_verification": "native_observation_matches" if report["native_witness"] else "decoded_without_native_observation",
            "reader_sha256": report["reader_sha256"],
            "replayed_sha256": [row["source_sha256"] for row in replays],
            "base": subprocess.check_output(
                ["git", "-C", root, "rev-parse", "HEAD"], text=True
            ).strip(),
        },
    )
