# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import subprocess

from convert.Formats.Fusion.Topology.BodyAnchor import KBodyGuid
from InferenceGrid.MeasureBodies import near


def fields(group):
    return {row["fields"]["FieldName"]: row["fields"]["Value"] for row in group["Fields"]["tuple"]}


def cached_bodies(native):
    result = []
    for segment in native["fields"]["Segments"]["tuple"]:
        records = segment["fields"]
        sid = records["Metadata"]["fields"]["Header"]["fields"]["SegmentId"]
        for record in records["Records"]["tuple"]:
            obj = record["fields"]
            groups = [group["fields"] for group in obj["Groups"]["tuple"]]
            if not obj["IsPrimary"] or not groups or groups[0]["ClassGuid"].upper() != KBodyGuid:
                continue
            properties = fields(groups[0])
            cache = properties.get("cache")
            values = {}
            if isinstance(cache, dict):
                for group in cache.get("fields", {}).get("Groups", {}).get("tuple", []):
                    values.update(fields(group["fields"]))
            cog = values.get("cog")
            center = fields(cog["fields"]) if isinstance(cog, dict) and "Fields" in cog.get("fields", {}) else {}
            result.append({"segment": sid, "object": obj["ObjectId"], "stored_name": properties.get("userName"),
                           "creation_index": properties.get("creationIndex"), "volume_cm3": values.get("volume"),
                           "area_cm2": values.get("area"), "center_cm": [center.get(axis) for axis in "xyz"]})
    return result


def capture_names(root, pin, size, native):
    bodies = cached_bodies(native)
    search = subprocess.run(["git", "-C", root, "grep", "-l", "-F", "-e", pin, "HEAD", "--",
                             "re/Fusion/LocalOracle/*/Controls/Capture*.json"], capture_output=True, timeout=60)
    if search.returncode not in (0, 1):
        search.check_returncode()
    witnesses = []
    for blob in search.stdout.decode().splitlines():
        if int(subprocess.check_output(["git", "-C", root, "cat-file", "-s", blob])) > 16 * 1024 * 1024:
            continue
        raw = subprocess.check_output(["git", "-C", root, "cat-file", "blob", blob])
        report = json.loads(raw)
        for case in report.get("controls", []):
            if not isinstance(case, dict) or (case.get("sha256"), case.get("bytes"), case.get("status")) != (pin, size, "captured"):
                continue
            measured = case.get("observed", {}).get("bodies", [])
            matches = []
            for body in bodies:
                candidates = []
                for idx, value in enumerate(measured):
                    center = value.get("center_cm")
                    if (isinstance(center, list) and len(center) == 3 and
                        all(near(a, b, 1e-6) for a, b in zip(center, body["center_cm"])) and
                        all(near(body[key], value.get(key), 1e-6) for key in ("volume_cm3", "area_cm2"))):
                        candidates.append(idx)
                matches.append(candidates)
            ids = [items[0] for items in matches if len(items) == 1]
            bijective = bool(bodies) and len(bodies) == len(measured) == len(ids) == len(set(ids))
            aligned = []
            if bijective:
                for body, index in zip(bodies, ids):
                    aligned.append({"object": body["object"], "segment": body["segment"], "stored_name": body["stored_name"],
                                    "creation_index": body["creation_index"], "vendor_name": measured[index]["name"]})
            witnesses.append({"capture": blob, "sha256": hashlib.sha256(raw).hexdigest(), "case": case["name"],
                              "unique_geometry_match": bijective, "candidate_indices": matches, "matches": aligned})
    return {"input_sha256": pin, "bodies": bodies, "witnesses": witnesses}
