from convert.adapters.solidworks.Drawing.Construction.Sheet.ImperialZones import (
    KImperialZones,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MetricZones import (
    KMetricZones,
)


# default zones must follow native thresholds and clamps for the authored document unit
def MakeSheetZones(LengthUnit: str) -> tuple[int, int, float, float]:
    if LengthUnit not in (
        "mm",
        "cm",
        "m",
        "in",
        "ft",
        "angstrom",
        "nm",
        "um",
        "mil",
        "microinch",
    ):
        raise ValueError("drawing sheet zones require a qualified document length unit")
    IsMetric = LengthUnit in ("mm", "cm", "m", "angstrom", "nm", "um")
    ZoneRows = KMetricZones if IsMetric else KImperialZones
    MarginValue = 0.01 if IsMetric else 0.5 * 0.0254
    Results: list[tuple[int, float]] = []
    for AxisValue in (11 * 0.0254, 8.5 * 0.0254):
        CountValue = 1
        for IndexValue, (LimitValue, ZoneCount) in enumerate(ZoneRows):
            if LimitValue <= AxisValue and (
                IndexValue + 1 == len(ZoneRows)
                or AxisValue < ZoneRows[IndexValue + 1][0] - 1e-8
            ):
                CountValue = ZoneCount
                break
        Results.append((CountValue, min(MarginValue, AxisValue * 0.5 - 0.005)))
    return Results[0][0], Results[1][0], Results[0][1], Results[1][1]
