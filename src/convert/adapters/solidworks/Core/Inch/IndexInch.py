from __future__ import annotations as Annotations

from convert.adapters.solidworks.Core.NativeScalar import NativeScalar


# feature owned name indexing preserves ambiguity checks across many dimensions
def IndexInch(Scalars: tuple[NativeScalar, ...]) -> dict[str, tuple[NativeScalar, ...]]:
    NamedScalars: dict[str, list[NativeScalar]] = {}
    for Scalar in Scalars:
        NamedScalars.setdefault(Scalar.name, []).append(Scalar)
    return {NameValue: tuple(Values) for NameValue, Values in NamedScalars.items()}
