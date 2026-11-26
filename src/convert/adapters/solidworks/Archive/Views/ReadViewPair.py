from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.CheckViewRep import CheckViewRep
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# a source camera needs separate orientation and pan zoom owners without accepting unrepresented perspective state
def ReadViewPair(ModelValue: object, PanValue: object) -> ViewInput:
    if not isinstance(ModelValue, Mapping) or not isinstance(PanValue, Mapping):
        raise ValueError("source camera requires two concrete transform records")
    ModelFields = CastValue(Mapping[str, object], ModelValue)
    PanFields = CastValue(Mapping[str, object], PanValue)
    FlagValues = (
        ModelFields.get("has_matrix"),
        PanFields.get("has_matrix"),
        ModelFields.get("f78"),
        PanFields.get("f78"),
    )
    if any(type(Value) is not int for Value in FlagValues) or FlagValues not in (
        (0, 0, 0, 0),
        (1, 0, 0, 0),
    ):
        raise ValueError("source camera requires ordinary orthographic transform modes")
    ScalarNames = {"has_matrix", "f58", "f60", "f68", "f70", "f78"}
    if set(ModelFields) != ScalarNames | ({"f08"} if FlagValues[0] else set()):
        raise ValueError("source camera orientation has absent or unrepresented fields")
    if set(PanFields) != ScalarNames:
        raise ValueError("source camera pan zoom has absent or unrepresented fields")
    if FlagValues[0]:
        MatrixValue = ModelFields["f08"]
        if not isinstance(MatrixValue, Mapping):
            raise ValueError("source camera orientation requires its actual matrix")
        MatrixFields = CastValue(Mapping[str, object], MatrixValue)
        if set(MatrixFields) != {f"m{Index}" for Index in range(9)}:
            raise ValueError("source camera matrix has absent or unrepresented fields")
        MatrixValues = tuple(
            RequireScalar(MatrixFields[f"m{Index}"]) for Index in range(9)
        )
    else:
        MatrixValues = tuple(float(Index % 4 == 0) for Index in range(9))
    ViewValue = ViewInput(
        MatrixValues,
        (
            RequireScalar(PanFields["f58"]),
            RequireScalar(PanFields["f60"]),
            RequireScalar(PanFields["f68"]),
        ),
        RequireScalar(PanFields["f70"]),
    )
    CheckViewRep(ModelFields, PanFields, ViewValue)
    return ViewValue
