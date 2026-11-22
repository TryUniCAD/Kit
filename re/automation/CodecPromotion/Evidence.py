# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib

from Artifacts import Artifacts
from InferenceInputs import checksum, parse_metadata, read_file
from StoreRead import read_store


def evidence(store, job, receipt_pin):
    checksum(receipt_pin)
    objects = Artifacts(store, create=False)
    with read_store(store.resolve() / "ledger.sqlite3", None, (4,)) as db:
        row = db.execute(
            "SELECT state,kind,result,fingerprint,generation,attempts,receipt FROM jobs WHERE id=?",
            (job,),
        ).fetchone()
        if not row or row["state"] != "completed" or row["receipt"] != receipt_pin:
            raise ValueError("a current completed inference receipt is required")

        def record(pin):
            raw = read_file(objects.path(pin), 4 * 1024 * 1024)
            if hashlib.sha256(raw).hexdigest() != pin:
                raise ValueError("stored proof digest mismatch")
            return parse_metadata(raw)

        receipt = record(receipt_pin)
        if any(receipt.get(key) != expected for key, expected in (
            ("job_id", job), ("generation", row["generation"]), ("attempt", row["attempts"]),
            ("fingerprint", row["fingerprint"]), ("outcome", "completed"), ("result_sha256", row["result"]),
        )):
            raise ValueError("receipt differs from the settled job")
        result = record(row["result"])["result"]
        records = result["records"]
        assessment = records["assessment"]
        if result["outcome"] != "completed" or records["execution"]["fingerprint"] != row["fingerprint"] or records["kind"] != row["kind"]:
            raise ValueError("inference result differs from its receipt")
        if row["kind"] == "inference.paired-gap" and assessment["status"] == "corroborated":
            finding = assessment["hypothesis"]
        elif row["kind"] == "inference.fields" and assessment["status"] == "hypothesis":
            (candidate,) = assessment["hypotheses"]
            if not candidate["holdout"] or candidate["confidence"] != "partial" or assessment["counterexamples"]:
                raise ValueError("field hypothesis lacks independent support")
            finding = {key: candidate[key] for key in ("relative_offset", "encoding")}
        else:
            raise ValueError("unresolved or refuted inference cannot generate codec code")
        return {"scope": records["scope"], "kind": row["kind"], "finding": finding}, set(records["source_sha256"])
