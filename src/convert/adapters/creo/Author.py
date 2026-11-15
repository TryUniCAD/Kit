from __future__ import annotations

from struct import pack as PackValue

KProductLine = (
    b"#Creo  TM  Version P-60-34  (c) 2019 by PTC Inc.  All Rights Reserved. 6.0.3.0\n"
)
KTocVersion = "1934"

KDoublePrefix = {0x40: b"\x46", 0xC0: b"\x2D", 0x3F: b"\x28", 0xBF: b"\x4F"}
KTocKind = "9"
KTocWidth = 81


def IntValue(Value: int) -> bytes:
    if 0 <= Value <= 0x7F:
        return bytes((Value,))
    if 0 <= Value <= 0x3FFF:
        return bytes((0x80 | (Value >> 8), Value & 0xFF))
    if 0 <= Value <= 0x1FFFFF:
        return bytes((0xC0 | (Value >> 16), (Value >> 8) & 0xFF, Value & 0xFF))
    return b"\xE8" + Value.to_bytes(3, "big")


def DoubleValue(Value: float) -> bytes:
    RawValue = PackValue(">d", Value)
    if RawValue[0] in (0x40, 0xC0) and RawValue[7] == 0x00:
        return KDoublePrefix[RawValue[0]] + RawValue[1:8]
    return b"\x52" + RawValue


def CompactDouble(Value: float) -> bytes:
    RawValue = PackValue(">d", Value)
    Prefix = KDoublePrefix.get(RawValue[0])
    if Prefix is not None:
        return Prefix + RawValue[1:8]
    return b"\x52" + RawValue


def NameValue(NameText: str) -> bytes:
    return b"\xE0\x01" + NameText.encode("latin-1") + b"\x00"


def StructHeader(NameText: str) -> bytes:
    return b"\xE0\x00" + NameText.encode("latin-1") + b"\x00"


def ChecksumValue(BodyValue: bytes) -> int:
    return sum(BodyValue) & 0xFFFF


def TocRow(
    NameText: str,
    OffsetValue: int,
    LengthValue: int,
    ExpandedValue: int,
    ChecksumValueA: int,
    ChecksumValueB: int,
) -> bytes:
    RowText = (
        f"{NameText} {OffsetValue:x} {LengthValue:x} {ExpandedValue:x} "
        f"{KTocVersion} {KTocKind} -1 {ChecksumValueA:04x} {ChecksumValueB:04x}"
    )
    return RowText.encode("ascii").ljust(KTocWidth - 1, b"#")[: KTocWidth - 1] + b"\n"


def HeaderLine(TextValue: str) -> bytes:
    return TextValue.encode("latin-1").ljust(68, b" ")[:68] + b" \\\n"


def BuildContainer(
    Sections: tuple[tuple[str, bytes], ...], ModelName: str = "box.prt"
) -> bytes:
    FirstLine = b"#UGC:2 PART 1934 1460 800 1 1 15 3700 2019344 00000000 \\"
    NameText = ModelName.encode("latin-1")
    NameLength = f"{len(NameText):03x}"
    HeaderBody = HeaderLine("#- VERS 0 0")
    HeaderBody += HeaderLine("#- HOST")
    HeaderBody += HeaderLine("#- LINK")
    HeaderBody += HeaderLine("#- DBID")
    HeaderBody += HeaderLine("#- REVS 0,")
    HeaderBody += HeaderLine("#- RELL 0,")
    HeaderBody += HeaderLine("#- UOBJ_ID 1 1 1")
    HeaderBody += HeaderLine("#- MACH _Windows")
    HeaderBody += HeaderLine("#- CMNM " + NameLength + ModelName)
    HeaderBody += b"#-END_OF_UGC_HEADER\n"
    Header = FirstLine + b"\n" + HeaderBody
    BaseValue = len(Header)
    Header = Header.replace(b"00000000", f"{BaseValue:08x}".encode("ascii"), 1)
    TocHead = (
        f"#UGC_TOC 2 {len(Sections)} {KTocWidth} 17".encode("ascii")
        .ljust(KTocWidth - 1, b"#")[: KTocWidth - 1]
        + b"\n"
    )
    BodyStart = BaseValue + len(KProductLine) + len(TocHead) + KTocWidth * len(Sections)
    Rows = b""
    Payloads = b""
    for NameText, PayloadValue in Sections:
        SectionValue = b"#" + NameText.encode("latin-1") + b"\n" + PayloadValue
        Relative = BodyStart + len(Payloads) - BaseValue
        Rows += TocRow(
            NameText,
            Relative,
            len(SectionValue),
            len(PayloadValue),
            ChecksumValue(PayloadValue),
            0,
        )
        Payloads += SectionValue + b"#\n"
    return Header + KProductLine + TocHead + Rows + Payloads + b"#END_OF_UGC\n"


def AuthorFeaturePayload(Features: tuple[tuple[int, int], ...]) -> bytes:
    Payload = StructHeader("Sld_Features") + b"\xE3"
    if not Features:
        return Payload + StructHeader("first_feat_ptr") + b"\xE3"
    Payload += StructHeader("first_feat_ptr") + b"\xE3"
    for IndexValue, (FeatureValue, ClassValue) in enumerate(Features):
        if IndexValue > 0:
            Payload += StructHeader("next_feat_ptr") + b"\xE3"
        Payload += NameValue("id") + IntValue(FeatureValue)
        Payload += NameValue("type") + IntValue(ClassValue)
    Payload += StructHeader("next_feat_ptr") + b"\x00"
    return Payload


def AuthorPart(Features: tuple[tuple[int, int], ...]) -> bytes:
    Sections = (("AllFeatur", AuthorFeaturePayload(Features)),)
    return BuildContainer(Sections)


def PlaneValues(
    NormalValue: tuple[float, float, float],
    OriginValue: tuple[float, float, float],
) -> tuple[float, ...]:
    if NormalValue == (0.0, 1.0, 0.0):
        Basis = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    elif NormalValue == (-0.0, 1.0, 0.0):
        Basis = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    elif NormalValue == (1.0, 0.0, 0.0):
        Basis = ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    elif NormalValue == (-1.0, 0.0, 0.0):
        Basis = ((0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
    elif NormalValue == (0.0, 0.0, 1.0):
        Basis = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    else:
        Basis = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0))
    FirstValue, SecondValue = Basis
    return (
        *FirstValue,
        *SecondValue,
        *NormalValue,
        *OriginValue,
    )


def PlaneDefine(GeomValue: int, Values: tuple[float, ...]) -> bytes:
    Payload = NameValue("geom_id") + IntValue(GeomValue)
    Payload += NameValue("geom_type") + IntValue(34)
    Payload += NameValue("feat_id") + IntValue(74)
    Payload += b"\xE0\x02envlp\x00\xF9" + IntValue(2) + IntValue(2)
    Payload += b"".join(DoubleValue(Value) for Value in (0.0, 1.0, 1.0, 0.0))
    Payload += b"\xE0\x02outline\x00\xF9" + IntValue(2) + IntValue(3)
    Payload += b"".join(DoubleValue(Value) for Value in (0.0, 0.0, 1.0, 0.0, 1.0, 1.0))
    Payload += b"\xE0\x02local_sys\x00\xF9" + IntValue(4) + IntValue(3)
    Payload += b"".join(DoubleValue(Value) for Value in Values)
    return Payload


def PlaneReplay(GeomValue: int, Values: tuple[float, ...]) -> bytes:
    Payload = b"\xE3" + IntValue(GeomValue) + IntValue(34) + IntValue(74)
    Payload += b"\xF9" + IntValue(2) + IntValue(2)
    Payload += b"".join(DoubleValue(Value) for Value in (0.0, 1.0, 1.0, 0.0))
    Payload += b"\xF9" + IntValue(2) + IntValue(3)
    Payload += b"".join(DoubleValue(Value) for Value in (0.0, 0.0, 1.0, 0.0, 1.0, 1.0))
    Payload += b"\xF9" + IntValue(4) + IntValue(3)
    Payload += b"".join(DoubleValue(Value) for Value in Values)
    return Payload


def AuthorGeometryPayload(
    Minimum: tuple[float, float, float], Maximum: tuple[float, float, float]
) -> bytes:
    XMinValue, YMinValue, ZMinValue = Minimum
    XMaxValue, YMaxValue, ZMaxValue = Maximum
    Planes = (
        ((-0.0, 1.0, 0.0), (0.0, YMaxValue, 0.0)),
        ((0.0, 1.0, 0.0), (0.0, YMinValue, 0.0)),
        ((1.0, 0.0, 0.0), (XMinValue, 0.0, 0.0)),
        ((-1.0, 0.0, 0.0), (XMaxValue, 0.0, 0.0)),
        ((0.0, 0.0, 1.0), (0.0, 0.0, ZMinValue)),
        ((0.0, 0.0, -1.0), (0.0, 0.0, ZMaxValue)),
    )
    Payload = StructHeader("Sld_VisGeom") + b"\xE3"
    Payload += StructHeader("active_geom") + b"\xE2"
    Payload += StructHeader("srf_array") + b"\xF8" + IntValue(len(Planes))
    Payload += b"\xF7" + IntValue(3) + b"\xFB\xE3"
    for IndexValue, (NormalValue, OriginValue) in enumerate(Planes):
        Values = PlaneValues(NormalValue, OriginValue)
        if IndexValue == 0:
            Payload += PlaneDefine(77 + IndexValue, Values)
        else:
            Payload += PlaneReplay(77 + IndexValue, Values)
    return Payload


def AuthorBox(
    Minimum: tuple[float, float, float],
    Maximum: tuple[float, float, float],
    Features: tuple[tuple[int, int], ...] = (
        (7, 923),
        (5, 923),
        (3, 923),
        (11, 979),
        (74, 917),
    ),
) -> bytes:
    Sections = (
        ("AllFeatur", AuthorFeaturePayload(Features)),
        ("VisibGeom", AuthorGeometryPayload(Minimum, Maximum)),
    )
    return BuildContainer(Sections)


def CloseValue(Level: int) -> bytes:
    return bytes((0xF0 + Level,))


def StructBegin(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xE3"


def NullStruct(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xE1"


def OpenStruct(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xE2"


def IntArrayStruct(NameText: str, Values: tuple[int, ...]) -> bytes:
    Payload = b"\xE0\x01" + NameText.encode("latin-1") + b"\x00"
    Payload += b"\xF8" + IntValue(len(Values))
    for Value in Values:
        Payload += IntValue(Value)
    return Payload


def SectionValue(NameText: str, Payload: bytes) -> bytes:
    return b"#" + NameText.encode("latin-1") + b"\n" + Payload


def EmptySectionPayloads() -> dict[str, bytes]:
    return {
        "Notes": SectionValue(
            "Notes", StructBegin("Sld_Notes") + CloseValue(1)
        ),
        "PipeInfos": SectionValue(
            "PipeInfos",
            StructBegin("Sld_PipeInfo") + NullStruct("piping_info") + CloseValue(1),
        ),
        "AssMrgPrt": SectionValue(
            "AssMrgPrt", StructBegin("assem_merge_parts") + CloseValue(1)
        ),
        "NeuAsmSld": SectionValue(
            "NeuAsmSld",
            StructBegin("Sld_NeutAssem") + NullStruct("neut_assem") + CloseValue(1),
        ),
        "FamilyInf": SectionValue(
            "FamilyInf",
            StructBegin("Sld_FamilyInfo") + NullStruct("drv_tbl_ptr") + CloseValue(1),
        ),
        "Hatching": SectionValue(
            "Hatching",
            StructBegin("Sld_Hatching")
            + OpenStruct("hatch_data_save_xar")
            + CloseValue(2),
        ),
        "Xsections": SectionValue(
            "Xsections",
            StructBegin("Sld_Xsections")
            + NullStruct("xsec_data")
            + OpenStruct("xsec_geom")
            + CloseValue(2),
        ),
        "DispDataColor": SectionValue(
            "DispDataColor", OpenStruct("ref_color_table") + CloseValue(1)
        ),
    }


def FeatureIndexPayload(Classes: tuple[int, ...]) -> bytes:
    return SectionValue(
        "FeatDefsIndex",
        StructBegin("Sld_FeatDefsIndex")
        + IntArrayStruct("feat_defs_index", Classes)
        + CloseValue(1),
    )


def FieldValue(TypeDigit: int, NameText: str, Value: bytes) -> bytes:
    return bytes((0xE0, TypeDigit)) + NameText.encode("latin-1") + b"\x00" + Value


def RefArrayValue(NameText: str, Count: int, Reference: int) -> bytes:
    Payload = (
        b"\xF8"
        + IntValue(Count)
        + b"\xF7"
        + IntValue(Reference)
        + b"\xFB"
    )
    return FieldValue(0, NameText, Payload)


def NeutralEmptyPayloads() -> dict[str, bytes]:
    return {
        "NovisGeom": SectionValue(
            "NovisGeom",
            StructBegin("Sld_NonVisGeom")
            + OpenStruct("inactive_geom")
            + StructHeader("external_geom")
            + CloseValue(1)
            + b"\xE2"
            + CloseValue(2),
        ),
        "BasFullData": SectionValue(
            "BasFullData",
            StructBegin("Sld_BasFullData")
            + RefArrayValue("dim_array", 3, 2)
            + b"\xE1\xE1\xE1"
            + FieldValue(1, "faceted_rep", CloseValue(1))
            + b"\x00"
            + CloseValue(1),
        ),
    }


def AuthoredSections(FeatureClasses: tuple[int, ...]) -> dict[str, bytes]:
    Bodies = EmptySectionPayloads()
    Bodies.update(NeutralEmptyPayloads())
    Bodies["FeatDefsIndex"] = FeatureIndexPayload(FeatureClasses)
    return Bodies


KMinimalStructs = (
    ("BasicData", "Sld_BasicData"),
    ("MdlStatus", "Sld_MdlStatus"),
    ("FullMData", "Sld_FullData"),
    ("LargeText", "Sld_LargeText"),
    ("BasicText", "Sld_BasicText"),
    ("Geomlists", "Sld_Geomlists"),
    ("GeomDepen", "Sld_GeomDepend"),
    ("DispCntrl", "Sld_DispCntrl"),
    ("ActEntity", "Sld_Entities"),
    ("NeuPrtSld", "Sld_NeutPart"),
    ("DwgData", "Sld_DwgData"),
    ("IdsGenInfoDb", "Sld_IdsGenInfoDb"),
    ("ActDatums", "Sld_ActDatums"),
    ("ModelView#0", "View"),
    ("ModelView#1073741824", "View"),
    ("ModelView#40", "View"),
    ("ModelView#41", "View"),
    ("ModelView#42", "View"),
    ("ModelView#43", "View"),
    ("ModelView#44", "View"),
    ("ModelView#45", "View"),
    ("ModelView#46", "View"),
    ("ModelView#48", "View"),
    ("ColorSchemeInfo", "color_scheme_ptr"),
    ("ColorSchemeInfoNew", "color_scheme_ptr_new"),
    ("THMB_IMG_INDX", "Thumbnail_indx_data"),
    ("CGFMappingTable", "pgl_cgf_map_array"),
)


def MinimalSections() -> dict[str, bytes]:
    return {
        NameText: SectionValue(
            NameText, StructBegin(StructName) + CloseValue(1)
        )
        for NameText, StructName in KMinimalStructs
    }


def EmptyPartSections(FeatureClasses: tuple[int, ...]) -> dict[str, bytes]:
    Bodies = AuthoredSections(FeatureClasses)
    Bodies.update(MinimalSections())
    Bodies["BasBasData"] = DefaultBasBasData()
    return Bodies


def ScalarValue(Value: float) -> bytes:
    if Value == 0.0:
        return b"\x18"
    if Value == 1.0:
        return b"\x0F"
    if Value == -1.0:
        return b"\x10"
    return CompactDouble(Value)


def RunValues(Values: tuple[float, ...]) -> bytes:
    Payload = b""
    IndexValue = 0
    while IndexValue < len(Values):
        Payload += ScalarValue(Values[IndexValue])
        RunLength = 1
        while (
            IndexValue + RunLength < len(Values)
            and Values[IndexValue + RunLength] == Values[IndexValue]
        ):
            RunLength += 1
        Extra = RunLength - 1
        if Extra == 1:
            Payload += b"\xE4"
        elif Extra == 2:
            Payload += b"\xE5"
        elif Extra == 3:
            Payload += b"\xE6"
        elif Extra > 3:
            Payload += b"\xE7" + IntValue(Extra)
        IndexValue += RunLength
    return Payload


def BasBasDataPayload(
    GeomRevision: int,
    CosmRevision: int,
    LayerCount: int,
    RelativeEpsilon: float,
    ModelEpsilon: float,
    PartType: int,
    FirstEntityId: int,
    Outline: tuple[float, ...],
    Attributes: tuple[int, ...],
    MaxPartSize: float,
) -> bytes:
    Payload = StructBegin("Sld_BasBasData")
    Payload += FieldValue(1, "tab_key", b"\x00")
    Payload += StructBegin("tab_key_struct")
    Payload += FieldValue(4, "type", IntValue(72))
    Payload += StructHeader("tab_key_ptr") + b"\xF8\x42"
    Payload += StructHeader("cmprs_tabkey") + CloseValue(1)
    Payload += b"\xE1"
    Payload += b"\xE0\x01type\x00" + CloseValue(1) + IntValue(2)
    Payload += StructBegin("revnum_ptr")
    Payload += FieldValue(1, "geom_revnum", IntValue(GeomRevision))
    Payload += FieldValue(1, "cosm_revnum", IntValue(CosmRevision))
    Payload += b"\xE0\x01insert_layer_id\x00" + CloseValue(1) + b"\xF6"
    Payload += FieldValue(1, "layer_count", IntValue(LayerCount))
    Payload += FieldValue(2, "rel_part_eps", ScalarValue(RelativeEpsilon))
    Payload += FieldValue(2, "model_eps", ScalarValue(ModelEpsilon))
    Payload += FieldValue(1, "fixed_model_eps", IntValue(0))
    Payload += FieldValue(1, "part_type", IntValue(PartType))
    Payload += FieldValue(1, "first_ent_id", IntValue(FirstEntityId))
    Payload += (
        FieldValue(2, "outline", b"\xF9\x02\x03" + RunValues(Outline))
    )
    Payload += (
        FieldValue(1, "attrib_array", b"\xF8" + IntValue(len(Attributes)))
        + b"".join(IntValue(Value) for Value in Attributes)
    )
    Payload += FieldValue(2, "max_part_size", ScalarValue(MaxPartSize))
    Payload += StructHeader("ref_part_tabs") + b"\xE3\xF2"
    return SectionValue("BasBasData", Payload)


def DefaultBasBasData() -> bytes:
    return BasBasDataPayload(
        124,
        30,
        1,
        0.0012,
        0.0,
        1,
        516377,
        (0.0,) * 6,
        (0,) * 21,
        0.0,
    )
