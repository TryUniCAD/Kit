# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import re
import subprocess

from convert.adapters.solidworks.Core.Dimensions.BindMirrorField import KMirroredFields
from InferenceGrid.SolidWorksFieldDiscovery import native_parameter_matches
from InferenceGrid.CandidateReader import decode_candidate

mirror_field_path = "src/convert/adapters/solidworks/Core/Dimensions/BindMirrorField.py"


def promote_fields(root, source, scratch, env, document, discovery, reader_root=None):
    if not discovery or not discovery["predictions"]:
        return None
    rows = discovery["predictions"]
    eligible = {tuple(r["key"]) for r in rows if r["keyword_matches"]}
    eligible.difference_update(tuple(r["key"]) for r in rows if not r["keyword_matches"])
    additions = {tuple(r["key"]): tuple(map(tuple, r["copies"])) for r in discovery["rules"]
                 if tuple(r["key"]) in eligible and tuple(r["key"]) not in KMirroredFields
                 and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", r["key"][0]) and re.fullmatch(r"D[1-9][0-9]{0,5}", r["key"][1])}
    if not additions:
        return None
    path = mirror_field_path
    reader_root = root if reader_root is None else reader_root
    original = (reader_root / path).read_text()
    start = original.index(" = {", original.index("KMirroredFields:")) + 3
    end = original.index("\n\n", start)
    lines = [f"    {key!r}: {offsets!r}," for key, offsets in sorted((KMirroredFields | additions).items())]
    updated = original[:start] + "{\n" + "\n".join(lines) + "\n}" + original[end:]
    replay = decode_candidate(root, reader_root, source, scratch, env, "field-rule-candidate", "document.json", path, updated)
    if replay is None:
        return None
    if replay["source"] != document["source"] or replay["source"]["sha256"] != discovery["input_sha256"]:
        return None
    targets = {(r["feature_id"], r["key"][1]): r for r in rows if tuple(r["key"]) in additions}
    owners = {f["id"]: f["attributes"].get("native_object_id") for f in document["feature_timeline"]["$tuple"]}
    before, after = [d["parameters"]["$tuple"] for d in (document, replay)]
    if [p["id"] for p in before] != [p["id"] for p in after]:
        return None
    checked = set()
    for old, new in zip(before, after):
        key = owners.get(old["owner_id"]), old["name"]
        if key not in targets:
            if old != new:
                return None
            continue
        r = targets[key]
        if key in checked or not native_parameter_matches(new, r):
            return None
        checked.add(key)
    if checked != targets.keys():
        return None
    patch = "".join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), "a/" + path, "b/" + path))
    return {"patch": patch, "verified_parameters": sorted(checked), "input_sha256": discovery["input_sha256"],
            "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()}
