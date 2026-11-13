from __future__ import annotations as Annotations
from dataclasses import replace as ReplaceData
import struct as Struct

from convert.adapters.solidworks.container.Archive import (
    Model,
    Node as NodeValue,
    encode_class_definition as EncodeClassDefinition,
    encode_string as EncodeString,
)
from convert.adapters.solidworks.container.Cmgr import (
    AddClassMut,
    AddDefMut,
    AddHeadMut,
    AddLinksMut,
    AddNullMut,
    AddObjectMut,
    CMgrParameters,
    DisplayStateA,
    IdentityBlock,
    KClassSchema,
    KDisplayChordRatio,
    KExtObjectClass,
    KMapBase,
    KObjectListClass,
    KObjectListTail,
    KRootClass,
    KStringHandleClass,
    KVisualMaterial,
    ReverseTable,
    StampList,
    StringHandle,
    Table,
    ValidateCmgr,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

KModernGeneration = 19000
KModernBuild = 2026306
KAppearanceId = 15000804
KVisualPrefixBytes = 465
KVisualBytes = 858
KDspbrBytes = 300
KTextureResource = (
    "C:\\PROGRA~1\\SOLIDW~1\\SOLIDW~1\\data\\graphics\\materials\\color.p2m"
)
KOpticsVector = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
KRvVector = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
KDisplayNextId = 120
KDisplayTail = ((0, 2), (0x0E00, 2), (0x259F, 2))
KDspbrScalars = (
    (0.8941177129745483, 0.8941177129745483, 0.8941177129745483),
    (0.0, 0.20000000298023224, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 1.5),
    (0.04000000283122063, 1.0, 1.0),
    (1.0, 1.0, 0.5),
    (0.0, 0.0, 0.0),
    (0.0, 1.0, 1.0),
    (1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 1.0, 100000.0),
    (0.8941177129745483, 0.8941177129745483, 0.8941177129745483),
    (0.0, 0.0, 0.0),
    (0.0,),
)
KNeutralStrings = ("", "", "", "", "basic")
KUpdatedAppearanceScalars = (
    1.0,
    0.0,
    0.4000000059604645,
    1.2999999523162842,
    1.0,
    1.0,
    1.0,
)


def EncodeText(Values: tuple[str, ...]) -> bytes:
    return b"".join(EncodeString(Value) for Value in Values)


def CheckedBytes(Value: bytes, Length: int, Label: str) -> bytes:
    if len(Value) != Length:
        raise SldprtFormatError(f"{Label} must contain {Length} bytes")
    return Value


def EncodeBase() -> bytes:
    return b"".join(
        (
            Struct.pack("<46f", *sum(KDspbrScalars, ())),
            Struct.pack("<II", 0, 1),
            EncodeText(KNeutralStrings),
            Struct.pack("<f", 1.0),
        )
    )


def EncodeGroup() -> bytes:
    return b"".join(
        (
            EncodeText(("2025x", "")),
            Struct.pack("<I", 0),
            Struct.pack("<6f", *KUpdatedAppearanceScalars[1:]),
            EncodeText(("", "")),
        )
    )


def EncodeTail() -> bytes:
    return Struct.pack("<2f", 1.0, 1.0) + EncodeText(("", "", ""))


def EncodeDspbr() -> bytes:
    return CheckedBytes(
        EncodeBase() + EncodeGroup() + EncodeTail(),
        KDspbrBytes,
        "2026 DSPBR",
    )


def EncodeRvTail() -> bytes:
    return b"".join(
        (
            EncodeString(KTextureResource),
            Struct.pack("<I2f", 0x00FFFFFF, 0.6000000238418579, 1.0),
            EncodeString(""),
            Struct.pack("<3f", 0.0010000000474974513, 0.0010000000474974513, 0.0),
            Struct.pack("<IIf", 320, 0, 0.0),
            Struct.pack("<8f", *KRvVector),
            Struct.pack("<4f", 1.0, 90.0, 1.0, -1.0),
            Struct.pack("<f", -1.0),
            EncodeString(""),
            Struct.pack("<f", 0.0),
        )
    )


def EncodeRvPrefix() -> bytes:
    return b"".join(
        (
            Struct.pack("<BI10f", 3, KAppearanceId, *KOpticsVector),
            Struct.pack("<I4f", 1, 0.05000000074505806, 0.0, -1.0, -1.0),
            Struct.pack("<fIf", -1.0, 0, 0.0),
            Struct.pack("<f", 0.0),
        )
    )


def EncodeVT() -> bytes:
    return b"".join(
        (
            EncodeString(""),
            Struct.pack("<II", 0, 0),
            EncodeString(""),
            Struct.pack("<II", 0, 1),
            EncodeString(""),
            Struct.pack("<IIIIII", 0, 1, 0xFFFFFFFF, 0, 0, 1),
        )
    )


def EncodeVP(RenderStyle: int) -> bytes:
    Material = Table(
        KVisualMaterial,
        {"appearance_id": KAppearanceId, "render_style": RenderStyle},
    )
    return Material + EncodeRvPrefix() + EncodeRvTail()


def EncodeVisual(Params: CMgrParameters) -> bytes:
    return EncodeDSP(
        Params.atom_ids[0], Params.generation, Params.build, Params.render_style
    )


def EncodeDSP(AtomId: int, Generation: int, Build: int, RenderStyle: int) -> bytes:
    return b"".join(
        (
            CheckedBytes(
                EncodeVP(RenderStyle), KVisualPrefixBytes, "2026 visual prefix"
            ),
            CheckedBytes(EncodeVT(), 52, "2026 visual tail"),
            EncodeDspbr(),
            IdentityBlock(AtomId, Generation, Build),
        )
    )


def EncodeDisplay(Params: CMgrParameters) -> bytes:
    NextId = KDisplayNextId if Params.next_id_a == 0 else Params.next_id_a
    Ratios = Params.chord_ratio if Params.chord_ratio != KDisplayChordRatio else 0.0
    ModernParams = ReplaceData(Params, next_id_a=NextId, chord_ratio=Ratios)
    return DisplayStateA(ModernParams)[:-6] + b"".join(
        Struct.pack("<H", Value) for Value, _ in KDisplayTail
    )


def AddTail(Params: CMgrParameters, Nodes: list[NodeValue], Config: int) -> None:
    AddNullMut(Nodes, Struct.pack("<III", 0, 1, 0xFFFFFFFF))
    AddNullMut(Nodes, b"")
    AddNullMut(Nodes, bytes(36))
    AddNullMut(Nodes, b"")
    AddNullMut(Nodes, b"")
    AddNullMut(Nodes, Struct.pack("<d", -1.0))
    AddNullMut(Nodes, Struct.pack("<d", 0.0))
    AddNullMut(Nodes, b"")
    AddNullMut(Nodes, ReverseTable(Params.reverse_atom_ids))
    AddObjectMut(Nodes, Config, Struct.pack("<IH", 1, 1))
    AddObjectMut(Nodes, Config, Struct.pack("<I", 1))
    _ = AddDefMut(Nodes, KExtObjectClass, b"")
    Handle = AddDefMut(Nodes, KStringHandleClass, EncodeString(""))
    AddClassMut(Nodes, Handle, StringHandle(Params))
    ObjList = AddDefMut(Nodes, KObjectListClass, StampList(Params.feature_stamps))
    AddClassMut(Nodes, ObjList, Table(KObjectListTail))


def BuildModel(Params: CMgrParameters) -> Model:
    ValidateCmgr(Params)
    if Params.generation != KModernGeneration:
        raise SldprtFormatError("2026 CMgr requires generation 19000")
    if len(Params.atom_ids) != 1:
        raise SldprtFormatError("2026 CMgr currently requires one solid feature atom")
    Nodes: list[NodeValue] = []
    Config = AddHeadMut(Nodes, Params)
    Nodes[1] = ReplaceData(
        Nodes[1],
        body=IdentityBlock(Params.atom_ids[0], Params.generation, Params.build),
    )
    Nodes[6] = ReplaceData(Nodes[6], body=EncodeVisual(Params))
    Nodes[8] = ReplaceData(Nodes[8], body=EncodeDisplay(Params))
    AddLinksMut(Nodes, Params)
    AddTail(Params, Nodes, Config)
    return Model(
        header=EncodeClassDefinition(KRootClass, KClassSchema),
        base=KMapBase,
        nodes=Nodes,
        Trailer=Struct.pack("<I", 0),
    )
