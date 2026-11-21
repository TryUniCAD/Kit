from math import comb as Combination


# polynomial integration preserves rectangular section moments at every height and taper sign
def DraftMoment(
    Width: float,
    Depth: float,
    Height: float,
    Slope: float,
    PowerX: int,
    PowerY: int,
    PowerZ: int,
) -> float:
    return sum(
        Combination(PowerX, Index)
        * Combination(PowerY, Other)
        * Width ** (PowerX - Index)
        * Depth ** (PowerY - Other)
        * (2 * Slope) ** (Index + Other)
        * Height ** (Index + Other + PowerZ + 1)
        / (Index + Other + PowerZ + 1)
        for Index in range(PowerX + 1)
        for Other in range(PowerY + 1)
    )
