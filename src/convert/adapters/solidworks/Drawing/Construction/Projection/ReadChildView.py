from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewOwners import (
    KViewDirections,
)


# drawing orientation must use the actual generated child canonical view and preserve its native matrix application order
def ReadChildView(
    ChildValue: PartCandidate, NameValue: str
) -> tuple[dict[str, object], tuple[tuple[float, ...], ...]]:
    if NameValue not in KViewDirections:
        raise ValueError("drawing projection requires a qualified named orientation")
    RowsValue = ChildValue.SystemValue.RootValue.FieldsValue["f9f8"]
    if not isinstance(RowsValue, (tuple, list)):
        raise ValueError("drawing child has no actual canonical views")
    NodesValue = tuple(
        NeedConceptNode(NeedConceptMap(RowValue)["o"], "moView_c")
        for RowValue in CastValue(Sequence[object], RowsValue)
    )
    Matches = tuple(
        NodeValue
        for NodeValue in NodesValue
        if NodeValue.FieldsValue["f358"] == NameValue
    )
    if len(Matches) != 1:
        raise ValueError("drawing orientation has no unique generated child owner")
    Rotation = dict(NeedConceptMap(Matches[0].FieldsValue["f368"]))
    AxesValue: tuple[tuple[float, ...], ...]
    if Rotation["has_matrix"] == 0:
        AxesValue = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    else:
        MatrixValue = dict(NeedConceptMap(Rotation["f08"]))
        Rotation["f08"] = MatrixValue
        AxesValue = tuple(
            tuple(
                NeedDrawNumber(MatrixValue[f"m{Index + 3 * Column}"])
                for Column in range(3)
            )
            for Index in range(3)
        )
    return Rotation, AxesValue
