# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import BrepPayload, CadDocument, PayloadRole


# extraction filters semantic brep payloads so unrelated native history remains embedded
def GetBrepPayloads(DocumentData: CadDocument) -> tuple[BrepPayload, ...]:
    return tuple(
        PayloadData
        for PayloadData in DocumentData.brep_payloads
        if PayloadData.role == PayloadRole.BREP and PayloadData.data is not None
    )
