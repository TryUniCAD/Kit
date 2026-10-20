# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue
from typing import Iterable as ValueIterable
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping


# wrapper metadata needs one reserved key shared by semantic filtering paths
KWrapperMetaKey = "kit.wrapper_metadata_keys"


# wrapper annotations must remain distinguishable from source semantic metadata
def AddWrapperMeta(
    MetaValues: TypeMap[str, AnyValue], KeyValues: ValueIterable[str]
) -> TypeMap[str, AnyValue]:
    ExistingValue = MetaValues.get(KWrapperMetaKey, ())
    NameValues = (
        {SourceValue for SourceValue in ExistingValue if isinstance(SourceValue, str)}
        if isinstance(ExistingValue, (tuple, list, set, frozenset))
        else set()
    )
    NameValues.update(
        SourceValue for SourceValue in KeyValues if isinstance(SourceValue, str)
    )
    ResultValue = dict(MetaValues)
    ResultValue[KWrapperMetaKey] = tuple(sorted(NameValues))
    return FreezeMapping(ResultValue)


# semantic comparisons must ignore metadata introduced only by transport wrappers
def GetSemanticMeta(
    MetaValues: TypeMap[str, AnyValue],
) -> TypeMap[str, AnyValue]:
    WrappedValues = MetaValues.get(KWrapperMetaKey, ())
    NameValues = (
        frozenset(
            SourceValue for SourceValue in WrappedValues if isinstance(SourceValue, str)
        )
        if isinstance(WrappedValues, (tuple, list, set, frozenset))
        else frozenset()
    )
    return FreezeMapping(
        {
            KeyValue: SourceValue
            for KeyValue, SourceValue in MetaValues.items()
            if KeyValue != KWrapperMetaKey and KeyValue not in NameValues
        }
    )
