# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict


# controller outcome summaries retain the independent native and portable acceptance boundaries
class OutcomeData(TypedDict):
    native_verified_samples: int
    portable_complete: bool
    status: str
    features: dict[str, dict[str, int]]
    samples: dict[str, dict[str, object]]
