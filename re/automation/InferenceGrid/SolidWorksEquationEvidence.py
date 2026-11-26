# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import math
import re

from convert.adapters.solidworks.Core.Native import ParseClasses, ParseNative
from InferenceInputs import read_file


def measured_values(observation):
    values = {}
    for feature in observation.get("feature_tree", []):
        for dimension in feature.get("dimensions", []):
            key = dimension["name"] + "@" + feature["name"]
            value = dimension.get("system_value")
            if key in values or type(value) not in (int, float) or not math.isfinite(value):
                values[key] = None
            else:
                values[key] = value
    return values


def trials(sets, pin, eligible):
    training = []
    held_out = None
    for folder, receipt, report, files in sets:
        if not any(row["sha256"] == pin for row in files.values()):
            continue
        for edit in report["observations"]["edits"]:
            name = edit["saved_file"]
            row = files.get(name)
            if not row or "/" in name or chr(92) in name or name in (".", ".."):
                continue
            raw = read_file(folder / name, 128 * 1024 * 1024)
            if len(raw) != row["size_bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                continue
            values = measured_values(edit["edited"])
            if row["sha256"] == pin:
                held_out = (values, edit["edited"].get("equations", []))
            elif row["sha256"] in eligible:
                training.append((row["sha256"], edit["parameter"], values, measured_values(edit["restored"])))
    return training, held_out


def close(left, right):
    return left is not None and right is not None and math.isclose(left, right, rel_tol=1e-11, abs_tol=1e-14)


def equation_evidence(streams, predictions, sets, pin, eligible):
    equations = []
    counts = {}
    for stream, data in streams.items():
        match = re.fullmatch(r"Contents/Config-([0-9]+)", stream)
        if match:
            rows = ParseNative(data, int(match[1]), stream)
            if not rows:
                continue
            managers = [c for c in ParseClasses(data) if c.name == "moRelMgr_c"]
            if len(managers) == 1:
                offset = managers[0].offset + 6 + len(managers[0].name)
                if offset + 2 <= len(data):
                    counts[stream] = (int.from_bytes(data[offset:offset + 2], "little"), len(rows))
            equations.extend(rows)
    if not equations:
        return []
    training, held = trials(sets, pin, eligible)
    results = []
    for eq in equations:
        local = {r["name"] + "@" + r["owner"]: r for r in predictions
                  if r.get("owner") and r.get("reader_span_matches") and r.get("neutral_value_matches") and
                  r["stream"] in (eq.native_stream, eq.native_stream + "-ResolvedFeatures")}
        native = {key: row["system_value"] for key, row in local.items()}
        declared, found = counts.get(eq.native_stream, (None, None))
        end = eq.native_offset + eq.native_length
        trailer = streams[eq.native_stream][end:end + 6] == bytes.fromhex("000200000000")
        result = {"target": eq.lhs, "source": eq.source, "stream": eq.native_stream, "offset": eq.native_offset,
                  "length": eq.native_length, "references": eq.references, "manager_count": declared,
                  "scanned_count": found, "relation_trailer_matches": trailer}
        results.append(result)
        if declared is None or declared != found or not trailer:
            result["status"] = "incomplete_relation_framing"
            continue
        literal = re.fullmatch(r"([-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s*(mm|deg)?", eq.rhs.strip())
        if "@" not in eq.lhs and literal and math.isfinite(float(literal[1])):
            result.update(status="saved_global_literal", value=float(literal[1]), explicit_unit=literal[2])
            continue
        match = re.fullmatch(r'\s*\(\s*"([^"]+)"\s*([+-])\s*"([^"]+)"\s*\)\s*/\s*([1-9][0-9]{0,2})\s*', eq.rhs)
        if not match:
            result["status"] = "unsupported_expression"
            continue
        left, operator, right, divisor = match.groups()
        if len({left, right, eq.lhs}) != 3:
            result["status"] = "dependent_or_repeated_reference"
            continue
        candidates = {(op, n) for op in ("+", "-") for n in range(1, 17)}
        independent = set()
        evidence = []
        for digest, parameter, edited, restored in training:
            keys = (left, right, eq.lhs)
            if any(edited.get(k) is None or restored.get(k) is None for k in keys):
                continue
            changes = [k for k in (left, right) if not close(edited[k], restored[k])]
            if len(changes) == 1 and changes[0].split("@", 1)[0] == parameter and not close(edited[eq.lhs], restored[eq.lhs]):
                independent.add(changes[0])
            for obs in (edited, restored):
                candidates = {(op, n) for op, n in candidates if close(
                    (obs[left] + obs[right] if op == "+" else obs[left] - obs[right]) / n, obs[eq.lhs])}
            evidence.append(digest)
        result.update(training_sha256=sorted(set(evidence)), independently_varied_operands=sorted(independent),
                      candidate_operations=sorted(candidates))
        if any(k not in native for k in (left, right, eq.lhs)):
            result["status"] = "missing_native_dimension"
            continue
        if len({local[k]["system_unit"] for k in (left, right, eq.lhs)}) != 1:
            result["status"] = "incompatible_operand_units"
            continue
        predicted = (native[left] + native[right] if operator == "+" else native[left] - native[right]) / int(divisor)
        result.update(predicted_system_value=predicted, saved_target=native[eq.lhs],
                      saved_value_matches=close(predicted, native[eq.lhs]))
        result["status"] = "saved_expression_replayed" if result["saved_value_matches"] else "saved_value_mismatch"
        if held is None:
            continue
        values, sources = held
        verified = eq.source in sources and all(close(values.get(k), native[k]) for k in (left, right, eq.lhs))
        result["vendor_edit_matches"] = verified
        if (verified and result["saved_value_matches"] and len(set(evidence)) >= 2 and
            independent == {left, right} and candidates == {(operator, int(divisor))}):
            result["status"] = "same_family_operands_varied"
    return results
