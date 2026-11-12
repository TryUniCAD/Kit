from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


def CheckTopology(
    Expected: tuple[AsmRecord, ...], Actual: AsmTable, Mapping: dict[int, int]
) -> None:
    for ExpectedId, Left in enumerate(Expected):
        Right = Actual.Records[Mapping[ExpectedId]]
        if Left.Name != Right.Name or len(Left.Tokens) != len(Right.Tokens):
            raise ValueError("Unsupported Fusion BRep record payload")
        for Index, (LeftToken, RightToken) in enumerate(
            zip(Left.Tokens, Right.Tokens, strict=True)
        ):
            if LeftToken[0] == 12:
                Reference = ReadAsmPtr(Left, Index)
                ExpectedRef = -1 if Reference == -1 else Mapping[Reference]
                if ReadAsmPtr(Right, Index) != ExpectedRef:
                    raise ValueError("Fusion BRep record reference disagrees")
            elif LeftToken != RightToken:
                raise ValueError("Unsupported Fusion BRep semantic field")
