# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from InferenceGrid.PromoteMirroredFields import mirror_field_path, promote_fields
from InferenceGrid.PromoteSketchCounts import promote_counts
from InferenceGrid.SolidWorksDimensionEvidence import dimension_evidence
from InferenceInputs import read_file


def reader_patches(root, reader, source, folder, env, document, evidence):
    field = promote_fields(
        root,
        source,
        folder,
        env,
        document,
        evidence.get("discovered_feature_fields"),
        reader,
    )
    if field:
        yield "mirrored-field-reader", field
    counts = promote_counts(root, source, folder, env, document, evidence, reader)
    if counts:
        yield "pattern-count-reader", counts


stages = {
    "mirrored-field-reader": (
        "field-rule-candidate",
        "document.json",
        mirror_field_path,
    ),
    "pattern-count-reader": (
        "pattern-candidate",
        "decoded.json",
        "src/convert/adapters/solidworks/Core/Native.py",
    ),
}


def reader_passes(root, source, scratch, env, document, evidence, controls=()):
    reader = root
    current = document
    history = []
    reports = {}
    touched = set()
    revisions = set()
    expected = {}
    for index in range(9):
        folder = scratch / f"reader-pass-{index}"
        folder.mkdir()
        if index == 0:
            standalone = dict(
                reader_patches(root, reader, source, folder, env, document, evidence)
            )
            reports.update(standalone)
            proposal = next(iter(standalone.items()), None)
        else:
            command = [
                sys.executable,
                "-m",
                "InferenceGrid.ReaderPass",
                str(root),
                str(reader),
                str(source),
                str(folder),
                str(output),
                *map(str, controls),
            ]
            child_env = {
                **env,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": os.pathsep.join(
                    map(str, (reader / "src", root / "Cli", root / "re/automation"))
                ),
            }
            subprocess.run(command, cwd=folder, env=child_env, check=True, timeout=480)
            evidence = json.loads(
                read_file(folder / "evidence.json", 128 * 1024 * 1024)
            )
            reports["candidate-dimension-evidence"] = evidence
            proposal = json.loads(read_file(folder / "proposal.json", 4 * 1024 * 1024))
        if not proposal:
            stop = "no_verified_patch"
            break
        if index == 8:
            stop = "pass_limit"
            break
        layer, receipt = proposal
        directory, filename, path = stages[layer]
        candidate = folder / directory
        output = candidate / filename
        replay = json.loads(read_file(output, 128 * 1024 * 1024))["document"]
        if (
            replay["source"] != document["source"]
            or receipt["input_sha256"] != document["source"]["sha256"]
        ):
            raise ValueError("candidate reader refers to a different input")
        params = {p["id"]: p for p in replay["parameters"]["$tuple"]}
        if any(params.get(k) != v for k, v in expected.items()):
            stop = "prior_prediction_changed"
            break
        ids = receipt["verified_parameters"]
        if layer == "mirrored-field-reader":
            owners = {
                f["id"]: f["attributes"].get("native_object_id")
                for f in replay["feature_timeline"]["$tuple"]
            }
            keys = set(map(tuple, ids))
            ids = [
                p["id"]
                for p in params.values()
                if (owners.get(p["owner_id"]), p["name"]) in keys
            ]
        previous = {p["id"]: p for p in current["parameters"]["$tuple"]}
        changed = [k for k in ids if params[k] != previous[k]]
        checksum = hashlib.sha256((candidate / path).read_bytes()).hexdigest()
        if (
            not ids
            or checksum == hashlib.sha256((reader / path).read_bytes()).hexdigest()
            or (path, checksum) in revisions
        ):
            stop = "no_new_reader_rule"
            break
        revisions.add((path, checksum))
        expected.update({k: params[k] for k in ids})
        touched.add(path)
        history.append(
            {
                "pass": index + 1,
                "generator": layer,
                "changed_parameters": changed,
                "verified_parameters": ids,
                "source_file_sha256": checksum,
            }
        )
        reader, current = candidate, replay
    if touched:
        patch = "".join(
            line
            for path in sorted(touched)
            for line in difflib.unified_diff(
                (root / path).read_text().splitlines(True),
                (reader / path).read_text().splitlines(True),
                "a/" + path,
                "b/" + path,
            )
        )
        reports["reader-patch"] = {
            "patch": patch,
            "input_sha256": document["source"]["sha256"],
            "base": subprocess.check_output(
                ["git", "-C", root, "rev-parse", "HEAD"], text=True
            ).strip(),
            "verified_parameters": sorted(expected),
        }
    reports["reader-passes"] = {
        "input_sha256": document["source"]["sha256"],
        "passes": history,
        "stop": stop,
    }
    return reports


if __name__ == "__main__":
    root, reader, source, folder, output, *controls = map(Path, sys.argv[1:])
    document = json.loads(read_file(output, 128 * 1024 * 1024))["document"]
    evidence = dimension_evidence(root, source, document["source"]["sha256"], document, controls)
    (folder / "evidence.json").write_text(json.dumps(evidence, allow_nan=False))
    proposal = next(
        reader_patches(root, reader, source, folder, os.environ, document, evidence),
        None,
    )
    (folder / "proposal.json").write_text(json.dumps(proposal))
