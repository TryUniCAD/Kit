# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.base.TransferContract import CarrierReason, TransferMode
from convert.adapters.base.WriteResult import WriteResult


# retained byte equality cannot promote unsupported graph editability or usability
def AssertReplay(Result: WriteResult, CaseName: str) -> None:
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    CanRebuild = CaseName == "supported"
    assert (
        Result.application_usable is CanRebuild and Result.vendor_loadable is CanRebuild
    )
    assert Result.metadata["application_usable"] is CanRebuild
    assert Result.metadata["vendor_loadable"] is CanRebuild
    Findings = tuple(
        Value
        for Value in Result.diagnostics
        if Value.code == "freecad.native_replay.unqualified"
    )
    if CanRebuild:
        assert not Findings and "unsupported_features" not in Result.metadata
        assert not Result.carrier_capabilities
    else:
        assert len(Findings) == 1 and Result.metadata["unsupported_features"]
        assert (
            Findings[0].attributes["unsupported_features"]
            == Result.metadata["unsupported_features"]
        )
        assert not Result.native_capabilities and Result.carrier_capabilities
        assert all(
            Value.mode is TransferMode.KCarrier
            and Value.carrier_reason is CarrierReason.KSourceOpaque
            for Value in Result.transfers
        )
