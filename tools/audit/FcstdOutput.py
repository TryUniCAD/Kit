# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import json as JsonData
from typing import Any as AnyValue


# state classification keeps human output aligned with machine readable verdict fields
def GetState(ResultData: dict[str, AnyValue]) -> str:
    if ResultData["application_usable"]:
        return "usable"
    if ResultData["vendor_loadable"]:
        return "vendor-only"
    if ResultData["error"]:
        return "error"
    return "unsupported"


# detail selection gives failures priority while retaining feature or requirement evidence
def GetDetail(ResultData: dict[str, AnyValue]) -> str:
    return (
        ResultData["error"]
        or ",".join(ResultData["feature_types"])
        or ",".join(ResultData["requirements"])
    )


# report rendering keeps json and concise terminal formats semantically equivalent
def PrintReport(
    ResultsData: tuple[dict[str, AnyValue], ...],
    SummaryData: dict[str, AnyValue],
    IsJson: bool,
) -> None:
    if IsJson:
        print(JsonData.dumps({"summary": SummaryData, "files": ResultsData}, indent=2))
        return
    for ResultData in ResultsData:
        StateValue = GetState(ResultData)
        DetailValue = GetDetail(ResultData)
        print(f"{StateValue:11} {ResultData['path']} {DetailValue}")
    print(JsonData.dumps(SummaryData, sort_keys=True))
