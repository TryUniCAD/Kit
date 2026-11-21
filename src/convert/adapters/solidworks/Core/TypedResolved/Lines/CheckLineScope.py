from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import (
    IsLineState,
)


# mixed curves and unqualified managers remain excluded while a separately validated dimension graph supplies its own admission
def CheckLineScope(
    FieldsValue: Mapping[str, object],
    HasDrivers: bool = False,
    HasRegions: bool = False,
) -> None:
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
    if not HasDrivers and not IsLineState(FieldsValue["dims"]):
        raise ValueError("typed line ring contains unqualified dimensions")
    if not all(
        IsLineState(FieldsValue[NameValue])
        for NameValue in (
            "f590",
            "coinc",
            "f580",
            "f598",
            "f588",
        )
    ):
        raise ValueError("typed line ring contains unqualified relation state")
    if not HasRegions and not IsLineState(FieldsValue["f5d8"]):
        raise ValueError("typed line ring contains unqualified region state")
