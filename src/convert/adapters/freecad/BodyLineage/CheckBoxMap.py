from collections.abc import Mapping

from convert.adapters.freecad.BodyLineage.BoxLineage import KBoxKind

# child aliases follow the three indexed groups of the observed map grammar
KMapKinds: tuple[tuple[KBoxKind, bytes, bytes], ...] = (
    ("edge", b"Edge", b"E"),
    ("face", b"Face", b"F"),
    ("vertex", b"Vertex", b"V"),
)


# only this map grammar can establish a source ordinal without native name overrides
def CheckBoxMap(MapData: bytes, ChildId: int, Counts: Mapping[KBoxKind, int]) -> None:
    Lines = tuple(Value.strip() for Value in MapData.splitlines() if Value.strip())
    if (
        len(Lines) != 20
        or Lines[:7]
        != (
            b"BeginElementMap v1",
            b"1 PostfixCount 3",
            b"Edge",
            b"Face",
            b"Vertex",
            b"MapCount 1",
            b"ElementMap 1 1 3",
        )
        or Lines[-1] != b"EndMap"
    ):
        raise ValueError("unsupported FreeCAD Body Shape element map framing")
    for IndexValue, (KindValue, Label, Suffix) in enumerate(KMapKinds):
        Start = 7 + IndexValue * 4
        Title, Children, Fields, Names = Lines[Start : Start + 4]
        Count = str(Counts[KindValue]).encode("ascii")
        TagValue = str(ChildId).encode("ascii")
        Postfix = f";:H{ChildId:x},".encode("ascii") + Suffix
        if (Title, Children, Names) != (
            Label,
            b"ChildCount 1",
            b"NameCount 0",
        ) or tuple(Fields.split()) != (
            b"1",
            b"0",
            Count,
            TagValue,
            b"0",
            Postfix,
            b"0",
        ):
            raise ValueError(
                "FreeCAD element map child range disagrees with its actual primitive"
            )
