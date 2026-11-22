from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)


# a periodic circular use closes on itself with no transmitted vertex
def MakeCircFin(
    FinValue: PrismRef,
    PairValue: PrismRef,
    LoopValue: PrismRef,
    EdgeValue: PrismRef,
    SenseValue: str,
) -> PrismCell:
    return PrismCell(
        FinValue,
        {
            "loop": LoopValue,
            "edge": EdgeValue,
            "other": PairValue,
            "forward": FinValue,
            "backward": FinValue,
            "vertex": 0,
            "next_at_vx": 0,
            "sense": SenseValue,
        },
    )
