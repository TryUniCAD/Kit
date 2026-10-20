# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.payloads.PayloadRoles import PayloadRole


# legacy payload inference needs declarative evidence that remains independently testable
@ModelDataMut(
    DefaultMap={
        "FormatIds": frozenset(),
        "Kinds": frozenset(),
        "Schemas": frozenset(),
        "SourceSuffixes": frozenset(),
    }
)
class PayloadRule(ModelBase):
    ValueRole: PayloadRole
    FileExtension: str
    FormatIds: frozenset[str]
    Kinds: frozenset[str]
    Schemas: frozenset[str]
    SourceSuffixes: frozenset[str]
