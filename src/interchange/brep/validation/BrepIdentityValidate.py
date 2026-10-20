# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import fields as GetFields

from interchange.brep.validation.BrepView import BrepView
from interchange.serialization.Wire import ResolveField


# identity indexing centralizes duplicate and empty identifier diagnostics
def GetBrepIds(
    ModelValue: BrepView,
) -> tuple[dict[str, frozenset[str]], tuple[str, ...]]:
    ErrorValues: list[str] = []
    IdentitySets: dict[str, frozenset[str]] = {}
    for FieldValue in GetFields(ModelValue):
        ModelName = ResolveField(type(ModelValue), FieldValue.name)
        if ModelName == "SchemaVersion":
            continue
        ItemValues = getattr(ModelValue, FieldValue.name)
        Identifiers = tuple(ItemValue.EntityId for ItemValue in ItemValues)
        if any(not Identifier for Identifier in Identifiers):
            ErrorValues.append(f"B-rep {FieldValue.name} contains an empty id")
        if len(Identifiers) != len(set(Identifiers)):
            ErrorValues.append(f"B-rep {FieldValue.name} contains duplicate ids")
        IdentitySets[ModelName] = frozenset(Identifiers)
    return IdentitySets, tuple(ErrorValues)
