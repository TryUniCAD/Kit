# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.base.TransferContract import (
    CapTransfer,
    CarrierReason,
    TransferMode,
)


# byte preservation alone cannot establish editable native capability support
def ReplayTransfers(
    Transfers: tuple[CapTransfer, ...], CanRebuild: bool
) -> tuple[CapTransfer, ...]:
    if CanRebuild:
        return Transfers
    return tuple(
        CapTransfer(
            Transfer.capability, TransferMode.KCarrier, CarrierReason.KSourceOpaque
        )
        for Transfer in Transfers
    )
