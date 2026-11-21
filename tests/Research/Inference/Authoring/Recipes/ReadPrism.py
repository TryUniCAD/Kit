# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as DecodeJson

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject


# negative semantic checks reuse authenticated native control measurements instead of inventing successful observations
def ReadPrism() -> dict[str, object]:
    Paths = list(
        (KRepoRoot / "re/automation/PairedCaptures/P03").glob(
            "solidworks-*/measurements.json"
        )
    )
    if len(Paths) != 1:
        raise ValueError("expected one retained native prism measurement report")
    ReportPath = Paths[0]
    Content = ReportPath.read_bytes()
    Receipt = DecodeJson(ReportPath.with_name("receipt.json").read_bytes())
    if Receipt["measurement_receipt_sha256"] != HashBytes(Content).hexdigest():
        raise ValueError("retained prism measurements differ from their native receipt")
    return ReadObject(
        ReadObject(ReadObject(DecodeJson(Content))["observations"])["baseline"]
    )
