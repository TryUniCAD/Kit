# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
from hashlib import sha256
from json import loads


# same-session observations cannot acquire fresh-process acceptance through the legacy verifier
def VerifyRoutine(Output, Report, CasePin):
    Receipt = loads((Output / "Routine.json").read_bytes())
    Manifest = Output.parent / "BatchManifest.json"
    First = loads((Output / Report["recipe_id"] / "first.json").read_bytes())
    Baseline = First["first_save"]
    if (
        Receipt["schema"] != 1
        or Receipt["mode"] != Report.get("verification_mode")
        or Receipt["mode"] != "document_reopen"
        or Receipt["configuration_sha256"] != CasePin
        or Receipt["manifest_sha256"] != sha256(Manifest.read_bytes()).hexdigest()
        or Receipt["pid"] != Report["authoring_process_id"]
        or Receipt["pid"] != Report["reopen_process_id"]
        or Receipt["created"] <= 0
        or Receipt["documents_before_reopen"] != 0
        or Receipt["documents_after"] != 0
        or Receipt["baseline_unloaded"] is not True
        or Receipt["baseline_sha256"] != Baseline["sha256"]
        or sha256((Output / Report["recipe_id"] / Baseline["file"]).read_bytes()).hexdigest() != Receipt["baseline_sha256"]
        or "fresh_reopen" in Report["observations"]
    ):
        raise ValueError("routine readback lacks closed-document and unchanged-file evidence")
