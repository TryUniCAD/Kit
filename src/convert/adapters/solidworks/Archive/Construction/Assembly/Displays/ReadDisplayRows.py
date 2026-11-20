from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)


# authored visibility rows must bind both actual occurrence identities without caller supplied wire ids
def ReadDisplayRows(
    DisplayValues: tuple[AsmDisplayIn, ...],
    Names: tuple[str, ...],
    FeatureIds: tuple[int, ...],
) -> tuple[tuple[str, dict[int, bool]], ...]:
    if type(DisplayValues) is not tuple or len(DisplayValues) != 3:
        raise ValueError(
            "assembly visibility requires the default and two opposite states"
        )
    States: list[tuple[str, dict[int, bool]]] = []
    Vectors: list[tuple[bool, ...]] = []
    for State in DisplayValues:
        if (
            type(State) is not AsmDisplayIn
            or type(State.NameValue) is not str
            or not State.NameValue.strip()
            or not State.NameValue.isprintable()
            or not State.NameValue.isascii()
            or type(State.VisibilityValues) is not tuple
            or any(
                type(RowValue) is not tuple
                or len(RowValue) != 2
                or type(RowValue[0]) is not str
                or type(RowValue[1]) is not bool
                for RowValue in State.VisibilityValues
            )
        ):
            raise ValueError(
                "assembly visibility requires named states and explicit Boolean occurrence values"
            )
        Visibility = dict(State.VisibilityValues)
        if len(State.VisibilityValues) != 2 or set(Visibility) != set(Names):
            raise ValueError(
                "assembly display state must bind both actual occurrences exactly once"
            )
        VectorValue = tuple(Visibility[NameValue] for NameValue in Names)
        Vectors.append(VectorValue)
        States.append(
            (State.NameValue, dict(zip(FeatureIds, VectorValue, strict=True)))
        )
    if (
        States[0][0] != "Display State-1"
        or len({NameValue.casefold() for NameValue, _ in States}) != 3
        or Vectors[0] != (True, True)
        or set(Vectors[1:]) != {(True, False), (False, True)}
    ):
        raise ValueError(
            "assembly visibility requires the all-visible default and distinct opposite states"
        )
    return tuple(States)
