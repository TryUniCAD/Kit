from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


def WritePatches(Regions: tuple[tuple[PatchCell, ...], ...]) -> str:
    Lines = ["0 " + str(len(Regions))]
    for Region in Regions:
        Words = [str(len(Region))]
        for CellValue in Region:
            Words.extend(
                str(Number)
                for Number in (CellValue.Face, *CellValue.Window, *CellValue.Offset)
            )
        Lines.append(" ".join(Words) + " ")
    return "\n".join(Lines) + "\n"
