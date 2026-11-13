from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PaperSize:
    PaperWidth: float
    PaperHeight: float
    PortWidth: float
    PortHeight: float
    TitleCorner: tuple[float, float]


KSheetSizes = {
    "A3 Landscape": PaperSize(420.0, 297.0, 673.449911, 325.726989, (410.0, 10.0)),
}


def SheetSize(SizeName: str) -> PaperSize:
    Paper = KSheetSizes.get(SizeName)
    if Paper is None:
        raise ValueError(f"Authored DWG sheet size {SizeName!r} is unsupported")
    return Paper
