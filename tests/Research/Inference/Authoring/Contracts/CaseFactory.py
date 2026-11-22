# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol


# native case creation retains its required keyword guard at the dynamic research boundary
class CaseFactory(Protocol):

    # explicit keyword ownership prevents invalid requests from losing their required case checks
    def __call__(
        self,
        Application: str,
        FeatureKey: str,
        Overrides: object,
        ModeValue: str,
        *,
        Required: bool = False,
    ) -> object:
        raise NotImplementedError
