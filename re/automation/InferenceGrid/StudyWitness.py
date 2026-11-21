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


def study_witness(root, pin, size, components):
    search = subprocess.run(
        ["git", "-C", root, "grep", "-l", "-F", "-e", pin, "HEAD", "--", "re/Fusion/Study/*/ground_truth.json"],
        capture_output=True, timeout=60,
    )
    if search.returncode == 1:
        return []
    search.check_returncode()
    witnesses = []
    for blob in search.stdout.decode().splitlines():
        if int(subprocess.check_output(["git", "-C", root, "cat-file", "-s", blob])) > 16 * 1024 * 1024:
            continue
        raw = subprocess.check_output(["git", "-C", root, "cat-file", "blob", blob])
        record = json.loads(raw)
        if not isinstance(record, dict) or record.get("terminal_status") != "complete" or record.get("errors") != []:
            continue
        for case in record.get("samples", []):
            export = case.get("export")
            if not isinstance(export, dict) or (export.get("sha256"), export.get("size_bytes"), export.get("returned_success")) != (pin, size, True):
                continue
            observed = case.get("feature_at_timeline_end")
            if not isinstance(observed, dict) or not observed.get("isValid") or observed.get("healthState") != 0 or any(
                item != [] for item in (case.get("getter_errors"), case.get("setter_errors"), observed.get("getter_errors"), observed.get("feature_getter_errors"))
            ):
                continue
            if case.get("phase") != "export_complete" or len(components) != 1:
                continue
            features = components[0]["features"]
            index = observed.get("timeline_index")
            if type(index) is not int or not 0 <= index < len(features):
                continue
            feature = features[index]
            checks = {"timeline_count": len(features) == case.get("timeline_count"),
                      "name": feature["name"] == observed.get("name"),
                      "suppression": feature["suppressed"] is observed.get("isSuppressed")}
            if observed.get("objectType") == "adsk::fusion::ExtrudeFeature":
                checks["class"] = feature["native_class"] == "DcExtrudeFeature"
                if type(observed.get("isThinExtrude")) is bool:
                    checks["thin"] = feature.get("thin") is observed["isThinExtrude"]
                enum = record.get("operation_enum_values", {})
                api_name = {"join": "JoinFeatureOperation", "cut": "CutFeatureOperation", "intersect": "IntersectFeatureOperation", "new": "NewBodyFeatureOperation"}.get(feature.get("operation"))
                if api_name in enum and type(observed.get("operation")) is int:
                    checks["operation"] = enum[api_name] == observed["operation"]
            witnesses.append({"record": blob, "record_sha256": hashlib.sha256(raw).hexdigest(),
                              "source_sha256": pin, "feature": feature["id"], "index": index,
                              "case": case.get("case"), "stage": "at_timeline_end_before_export", "checks": checks})
    return witnesses
