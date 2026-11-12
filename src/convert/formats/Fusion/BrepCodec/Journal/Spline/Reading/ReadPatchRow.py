from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


def ReadPatchRow(LineText: str) -> tuple[PatchCell, ...]:
    Words = LineText.split(" ")
    if len(Words) < 2 or Words[-1]:
        raise ValueError("Invalid Fusion T-spline patch row")
    Numbers = tuple(int(WordText) for WordText in Words[:-1])
    if not 0 < Numbers[0] <= 4096 or len(Numbers) != 1 + 8 * Numbers[0]:
        raise ValueError("Invalid Fusion T-spline patch row size")
    return tuple(
        PatchCell(
            Numbers[Start],
            (
                Numbers[Start + 1],
                Numbers[Start + 2],
                Numbers[Start + 3],
                Numbers[Start + 4],
            ),
            (Numbers[Start + 5], Numbers[Start + 6], Numbers[Start + 7]),
        )
        for Start in range(1, len(Numbers), 8)
    )
