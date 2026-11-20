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
from InferenceGrid.TraceRefusal import LOCAL


def fields(group):
    return {row["fields"]["FieldName"]: row["fields"]["Value"] for row in group["Fields"]["tuple"]}


def cached_bodies(native):
    result = []
    collections = {}
    owners = {}
    for segment in native["fields"]["Segments"]["tuple"]:
        records = segment["fields"]
        sid = records["Metadata"]["fields"]["Header"]["fields"]["SegmentId"]
        for record in records["Records"]["tuple"]:
            obj = record["fields"]
            groups = [group["fields"] for group in obj["Groups"]["tuple"]]
            if not obj["IsPrimary"] or not groups:
                continue
            if groups[0]["ClassGuid"].upper() == "CD57BC48-50EC-47DC-975A-FB6DEA72F4DA":
                children = fields(groups[0]).get("groupChildren")
                if isinstance(children, dict):
                    items = children.get("fields", {}).get("Items", {}).get("tuple")
                    if isinstance(items, list) and all(isinstance(child, dict) and child.get("record") == LOCAL for child in items):
                        ids = [child["fields"]["ObjectId"] for child in items]
                        key = (sid, obj["ObjectId"])
                        if len(set(ids)) == len(ids) and key not in collections:
                            collections[key] = {child: index for index, child in enumerate(ids, 1)}
                            for child in ids:
                                owners.setdefault((sid, child), []).append(obj["ObjectId"])
                        else:
                            collections[key] = None
            if groups[0]["ClassGuid"].upper() != KBodyGuid:
                continue
            properties = fields(groups[0])
            parent = properties.get("rGroupParent")
            collection = parent["fields"]["ObjectId"] if isinstance(parent, dict) and parent.get("record") == LOCAL else None
            cache = properties.get("cache")
            values = {}
            if isinstance(cache, dict):
                for group in cache.get("fields", {}).get("Groups", {}).get("tuple", []):
                    values.update(fields(group["fields"]))
            cog = values.get("cog")
            center = fields(cog["fields"]) if isinstance(cog, dict) and "Fields" in cog.get("fields", {}) else {}
            result.append({"segment": sid, "object": obj["ObjectId"], "stored_name": properties.get("userName"),
                           "collection": collection, "creation_index": properties.get("creationIndex"), "volume_cm3": values.get("volume"),
                           "area_cm2": values.get("area"), "center_cm": [center.get(axis) for axis in "xyz"]})
    for body in result:
        children = collections.get((body["segment"], body["collection"]))
        parents = owners.get((body["segment"], body["object"]), [])
        ordinal = children.get(body["object"]) if children is not None and parents == [body["collection"]] else None
        body["collection_ordinal"] = ordinal
        body["membership"] = "listed" if ordinal else "unlisted" if children is not None and not parents else "unresolved"
    return result


def default_name_rules(witnesses):
    observations = [body for witness in witnesses for body in witness["matches"] if body["stored_name"] == ""]
    rules = {}
    for field in ("creation_index", "collection_ordinal"):
        compared = [row for row in observations if type(row[field]) is int and row[field] > 0]
        failures = [{"segment": row["segment"], "object": row["object"], "observed": row["vendor_name"],
                     "predicted": f"Body{row[field]}"} for row in compared if f"Body{row[field]}" != row["vendor_name"]]
        rules[field] = {"compared": len(compared), "counterexamples": failures}
    if not observations:
        status = "no_measured_default_names"
    elif any(rule["compared"] < len(observations) for rule in rules.values()):
        status = "incomplete_native_fields"
    else:
        surviving = sum(not rule["counterexamples"] for rule in rules.values())
        status = ("both_refuted", "distinguished_on_input", "needs_distinguishing_control")[surviving]
    return {"status": status, "rules": rules,
            "next_capture": "RemoveFirstDefaultBody" if status == "needs_distinguishing_control" else None}


def capture_names(root, pin, size, native):
    bodies = cached_bodies(native)
    comparable = [body for body in bodies if body["membership"] != "unlisted"]
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
        if not isinstance(report, dict) or report.get("status") != "captured":
            continue
        for case in report.get("controls", []):
            if not isinstance(case, dict) or (case.get("sha256"), case.get("bytes"), case.get("status")) != (pin, size, "captured"):
                continue
            measured = case.get("observed", {}).get("bodies", [])
            if not isinstance(measured, list) or not all(isinstance(row, dict) and isinstance(row.get("name"), str) for row in measured):
                continue
            matches = []
            for body in comparable:
                candidates = []
                for idx, value in enumerate(measured):
                    center = value.get("center_cm")
                    single_without_centroid = len(comparable) == len(measured) == 1 and "center_cm" not in value
                    center_matches = isinstance(center, list) and len(center) == 3 and all(
                        near(a, b, 1e-6) for a, b in zip(center, body["center_cm"]))
                    if ((single_without_centroid or center_matches) and
                        all(near(body[key], value.get(key), 1e-6) for key in ("volume_cm3", "area_cm2"))):
                        candidates.append(idx)
                matches.append(candidates)
            ids = [items[0] for items in matches if len(items) == 1]
            bijective = bool(comparable) and all(body["membership"] == "listed" for body in comparable) and len(comparable) == len(measured) == len(ids) == len(set(ids))
            aligned = []
            if bijective:
                for body, index in zip(comparable, ids):
                    aligned.append({"object": body["object"], "segment": body["segment"], "stored_name": body["stored_name"],
                                    "creation_index": body["creation_index"], "collection_ordinal": body["collection_ordinal"],
                                    "geometry_fields": ["volume_cm3", "area_cm2"] + (["center_cm"] if "center_cm" in measured[index] else []),
                                    "vendor_name": measured[index]["name"]})
            timeline = case.get("observed", {}).get("timeline")
            names = [row["name"] for row in timeline] if isinstance(timeline, list) and all(
                isinstance(row, dict) and isinstance(row.get("name"), str) for row in timeline) else None
            witnesses.append({"timeline_names": names, "capture": blob, "sha256": hashlib.sha256(raw).hexdigest(), "case": case["name"],
                              "unique_geometry_match": bijective, "candidate_indices": matches, "matches": aligned})
    return {"input_sha256": pin, "bodies": bodies, "witnesses": witnesses, "default_name_rules": default_name_rules(witnesses)}
