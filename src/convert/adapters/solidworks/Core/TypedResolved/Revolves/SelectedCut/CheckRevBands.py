from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutBand import (
    RevCutBand,
)


# independent radial bands identify which cylindrical wall the explicit selected cutter reaches
def CheckRevBands(First: RevCutBand, Second: RevCutBand, CutBand: RevCutBand) -> None:
    if (
        First.Axial != Second.Axial
        or not First.Axial[0] < CutBand.Axial[0] < CutBand.Axial[1] < First.Axial[1]
        or not First.Radial[0]
        < CutBand.Radial[0]
        < First.Radial[1]
        < Second.Radial[0]
        < CutBand.Radial[1]
        < Second.Radial[1]
    ):
        raise ValueError(
            "selected revolve cut requires two distinct coaxial bands and an internal cutter crossing both walls"
        )
