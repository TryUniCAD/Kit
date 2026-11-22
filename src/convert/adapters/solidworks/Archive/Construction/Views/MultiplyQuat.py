# explicit native multiplication order preserves signed zero and rounding in compound canonical views
def MultiplyQuat(
    FirstValue: tuple[float, float, float, float],
    SecondValue: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    AlphaX, AlphaY, AlphaZ, AlphaW = FirstValue
    BravoX, BravoY, BravoZ, BravoW = SecondValue
    return (
        ((AlphaX * BravoW + BravoX * AlphaW) + AlphaY * BravoZ) - AlphaZ * BravoY,
        ((BravoY * AlphaW - BravoZ * AlphaX) + AlphaY * BravoW) + AlphaZ * BravoX,
        ((BravoY * AlphaX + BravoZ * AlphaW) - AlphaY * BravoX) + AlphaZ * BravoW,
        ((BravoW * AlphaW - AlphaX * BravoX) - AlphaY * BravoY) - AlphaZ * BravoZ,
    )
