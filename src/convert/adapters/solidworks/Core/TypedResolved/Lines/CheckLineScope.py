from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import (
    IsLineState,
)


# mixed curves dimensions and derived managers remain outside the ordinary unconstrained line ring profile
def CheckLineScope(FieldsValue: Mapping[str, object], *, HasDims: bool = False) -> None:
    OtherArrays = (
        "texts",
        "hatches",
        "arcs",
        "ellipses",
        "parabolas",
        "splines",
        "planes",
        "cylinders",
        "spheres",
        "cones",
        "parametric",
        "offsets",
        "sketch_offsets",
        "styled",
        "intersections",
        "tools",
        "blocks",
        "silhouettes",
    )
    if (
        any(FieldsValue[NameValue] for NameValue in OtherArrays)
        or FieldsValue.get("f568") != -1
    ):
        raise ValueError("typed line ring contains other geometry")
    if not all(
        IsLineState(FieldsValue[NameValue])
        for NameValue in (
            "dims",
            "f590",
            "coinc",
            "f5d8",
            "f580",
            "f598",
            "f588",
        )
        if NameValue != "dims" or not HasDims
    ):
        raise ValueError("typed line ring contains unqualified relation state")
