from __future__ import annotations

from struct import pack as PackValue

from convert.adapters.creo.Stream import StreamParser

# vendor banner text the loader uses to recognise a psb container
KProductLine = (
    b"#Creo  TM  Version P-60-34  (c) 2019 by PTC Inc.  All Rights Reserved. 6.0.3.0\n"
)

# every directory row must repeat the same schema version
KTocVersion = "1934"


# compact double lanes save twelve bytes on every stored scalar
KDoublePrefix = {0x40: b"\x46", 0xC0: b"\x2d", 0x3F: b"\x28", 0xBF: b"\x4f"}

# section rows default to the plain tagged stream kind
KTocKind = "9"

# directory rows are fixed width so offsets stay computable
KTocWidth = 81


# lengths and identifiers repeat everywhere so one encoder owns them
def IntValue(Value: int) -> bytes:
    if 0 <= Value <= 0x7F:
        return bytes((Value,))
    if 0 <= Value <= 0x3FFF:
        return bytes((0x80 | (Value >> 8), Value & 0xFF))
    if 0 <= Value <= 0x1FFFFF:
        return bytes((0xC0 | (Value >> 16), (Value >> 8) & 0xFF, Value & 0xFF))
    return b"\xe8" + Value.to_bytes(3, "big")


# geometry needs doubles emitted in the vendor compact form
def DoubleValue(Value: float) -> bytes:
    RawValue = PackValue(">d", Value)
    Prefix = KDoublePrefix.get(RawValue[0])
    if Prefix is not None:
        return Prefix + RawValue[1:]
    return b"\x52" + RawValue


# scalar lanes must stay compact or later lanes misalign
def CompactDouble(Value: float) -> bytes:
    RawValue = PackValue(">d", Value)
    Prefix = KDoublePrefix.get(RawValue[0])
    if Prefix is not None:
        return Prefix + RawValue[1:8]
    return b"\x52" + RawValue


# field names are length prefixed in the typed name lane
def NameValue(NameText: str) -> bytes:
    return b"\xe0\x01" + NameText.encode("latin-1") + b"\x00"


# every nested record begins with the same typed header
def StructHeader(NameText: str) -> bytes:
    return b"\xe0\x00" + NameText.encode("latin-1") + b"\x00"


# the directory stores a body checksum the loader verifies
def ChecksumValue(BodyValue: bytes) -> int:
    return sum(BodyValue) & 0xFFFF


# one owner keeps row formatting identical across tables
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


# the header is fixed width because the base offset is parsed from it
def HeaderLine(TextValue: str) -> bytes:
    return TextValue.encode("latin-1").ljust(68, b" ")[:68] + b" \\\n"


# whole part assembly lives here so callers cannot drift
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
        f"#UGC_TOC 2 {len(Sections)} {KTocWidth} 17".encode("ascii").ljust(
            KTocWidth - 1, b"#"
        )[: KTocWidth - 1]
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


# the feature chain is the minimum a part must declare
def AuthorFeaturePayload(Features: tuple[tuple[int, int], ...]) -> bytes:
    Payload = StructHeader("Sld_Features") + b"\xe3"
    if not Features:
        return Payload + StructHeader("first_feat_ptr") + b"\xe3"
    Payload += StructHeader("first_feat_ptr") + b"\xe3"
    for IndexValue, (FeatureValue, ClassValue) in enumerate(Features):
        if IndexValue > 0:
            Payload += StructHeader("next_feat_ptr") + b"\xe3"
        Payload += NameValue("id") + IntValue(FeatureValue)
        Payload += NameValue("type") + IntValue(ClassValue)
    Payload += StructHeader("next_feat_ptr") + b"\x00"
    return Payload


# keeps the older two section part available for tests
def AuthorPart(Features: tuple[tuple[int, int], ...]) -> bytes:
    Sections = (("AllFeatur", AuthorFeaturePayload(Features)),)
    return BuildContainer(Sections)


# plane frames repeat across prototypes so they decode once
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


# the first array element must carry every field header
def PlaneDefine(
    GeomValue: int,
    Values: tuple[float, ...],
    FeatureId: int = 74,
    NextGeomId: int = 82,
    Envelope: tuple[float, ...] = (0.0, 1.0, 1.0, 0.0),
    Outline: tuple[float, ...] = (0.0, 0.0, 1.0, 0.0, 1.0, 1.0),
) -> bytes:
    Payload = (
        b"\xe3"
        + NameValue("geom_id")
        + IntValue(GeomValue)
        + NameValue("geom_type")
        + IntValue(34)
        + NameValue("feat_id")
        + IntValue(FeatureId)
        + NameValue("orient")
        + SignedInt(-1)
        + NameValue("boundary_type")
        + SignedInt(0)
        + NameValue("next_geom_ptr")
        + SignedInt(NextGeomId)
    )
    Payload += b"\xe0\x02envlp\x00\xf9\x02\x02"
    Payload += RunValues(Envelope)
    Payload += b"\xe0\x02outline\x00\xf9\x02\x03"
    Payload += RunValues(Outline)
    Payload += StructHeader("srf_prim_ptr(plane)") + b"\xe3"
    Payload += b"\xe0\x02local_sys\x00\xf9\x04\x03"
    Payload += RunValues(Values)
    Payload += StructHeader("frst_cntr_ptr") + b"\xf1\xe3"
    Payload += NameValue("frst_cntr_crv_hdr_ptr") + IntValue(GeomValue + 1)
    Payload += NameValue("trv") + IntValue(1)
    Payload += b"\xe0\x02envlp\x00\xf9\x02\x02"
    Payload += RunValues(Envelope)
    Payload += StructHeader("next_cntr_ptr") + b"\xf1\xe1"
    Payload += StructHeader("topol_ref_data") + b"\xe3"
    Payload += NameValue("owner_feat_revnum") + IntValue(13)
    Payload += StructHeader("srf_flip_dat") + b"\xe1"
    Payload += NameValue("list_id") + SignedInt(-5778)
    Payload += NameValue("list_type") + IntValue(98)
    return Payload + b"\xf2"


# later array elements may not redeclare fields
def PlaneReplay(
    GeomValue: int,
    Values: tuple[float, ...],
    FeatureId: int = 74,
    NextGeomId: int = 82,
    Envelope: tuple[float, ...] = (0.0, 1.0, 1.0, 0.0),
    Outline: tuple[float, ...] = (0.0, 0.0, 1.0, 0.0, 1.0, 1.0),
) -> bytes:
    Payload = b"\xf7\x03\xe3" + IntValue(GeomValue) + IntValue(34) + IntValue(FeatureId)
    Payload += SignedInt(-1) + SignedInt(0) + SignedInt(NextGeomId)
    Payload += b"\xf9\x02\x02" + RunValues(Envelope)
    Payload += b"\xf9\x02\x03" + RunValues(Outline)
    Payload += b"\xe3"
    Payload += b"\xf9\x04\x03" + RunValues(Values)
    Payload += b"\xf1"
    Payload += b"\xf1\xe3" + IntValue(NextGeomId) + IntValue(1)
    Payload += b"\xf9\x02\x02" + RunValues(Envelope)
    Payload += b"\xf1\xe1"
    Payload += (
        b"\xe3" + IntValue(13) + b"\xe1" + SignedInt(-5778) + IntValue(98) + b"\xf2"
    )
    return Payload


# surfaces encode differently from features so they own a writer
def AuthorGeometryPayload(
    Minimum: tuple[float, float, float],
    Maximum: tuple[float, float, float],
    FeatureId: int = 74,
    FirstGeomId: int = 77,
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
    Extent = (
        max(XMaxValue - XMinValue, YMaxValue - YMinValue, ZMaxValue - ZMinValue) / 2.0
    )
    Envelope = (Extent, Extent, -Extent, -Extent)
    Outline = (Extent, 0.0, Extent, -Extent, 0.0, -Extent)
    Payload = StructHeader("Sld_VisGeom") + b"\xe3"
    Payload += StructHeader("active_geom") + b"\xe2"
    Payload += StructHeader("srf_array") + b"\xf8" + IntValue(len(Planes))
    Payload += b"\xf7" + IntValue(3) + b"\xfb\xe3"
    for IndexValue, (NormalValue, OriginValue) in enumerate(Planes):
        Values = PlaneValues(NormalValue, OriginValue)
        if IndexValue == 0:
            Payload += PlaneDefine(
                FirstGeomId + IndexValue,
                Values,
                FeatureId,
                FirstGeomId + 5,
                Envelope,
                Outline,
            )
        else:
            Payload += PlaneReplay(
                FirstGeomId + IndexValue,
                Values,
                FeatureId,
                FirstGeomId + 5,
                Envelope,
                Outline,
            )
    return Payload


# a known volume is the only way to check the mass code
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


# closing levels are positional so callers must not write raw bytes
def CloseValue(Level: int) -> bytes:
    return bytes((0xF0 + Level,))


# opening a record correctly is easy to get wrong
def StructBegin(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xe3"


# absent members still need their name on the wire
def NullStruct(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xe1"


# arrays and unions share the same opening token
def OpenStruct(NameText: str) -> bytes:
    return StructHeader(NameText) + b"\xe2"


# integer arrays appear in several sections so they share one emitter
def IntArrayStruct(NameText: str, Values: tuple[int, ...]) -> bytes:
    Payload = b"\xe0\x01" + NameText.encode("latin-1") + b"\x00"
    Payload += b"\xf8" + IntValue(len(Values))
    for Value in Values:
        Payload += IntValue(Value)
    return Payload


# every section body starts with its own name line
def SectionValue(NameText: str, Payload: bytes) -> bytes:
    return b"#" + NameText.encode("latin-1") + b"\n" + Payload


# these sections only need their root record to exist
def EmptySectionPayloads() -> dict[str, bytes]:
    return {
        "Notes": SectionValue("Notes", StructBegin("Sld_Notes") + CloseValue(1)),
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


# the loader cross checks this index against the feature chain
def FeatureIndexPayload(Classes: tuple[int, ...]) -> bytes:
    return SectionValue(
        "FeatDefsIndex",
        StructBegin("Sld_FeatDefsIndex")
        + IntArrayStruct("feat_defs_index", Classes)
        + CloseValue(1),
    )


# typed fields are the atom every section emitter builds from
def FieldValue(TypeDigit: int, NameText: str, Value: bytes) -> bytes:
    return bytes((0xE0, TypeDigit)) + NameText.encode("latin-1") + b"\x00" + Value


# reference arrays point at an earlier element by index
def RefArrayValue(NameText: str, Count: int, Reference: int) -> bytes:
    Payload = b"\xf8" + IntValue(Count) + b"\xf7" + IntValue(Reference) + b"\xfb"
    return FieldValue(0, NameText, Payload)


# neutral state sections are optional but must still parse
def NeutralEmptyPayloads() -> dict[str, bytes]:
    return {
        "NovisGeom": SectionValue(
            "NovisGeom",
            StructBegin("Sld_NonVisGeom")
            + OpenStruct("inactive_geom")
            + StructHeader("external_geom")
            + CloseValue(1)
            + b"\xe2"
            + CloseValue(2),
        ),
        "BasFullData": SectionValue(
            "BasFullData",
            StructBegin("Sld_BasFullData")
            + RefArrayValue("dim_array", 3, 2)
            + b"\xe1\xe1\xe1"
            + FieldValue(1, "faceted_rep", CloseValue(1))
            + b"\x00"
            + CloseValue(1),
        ),
    }


# callers need one place that lists every section we generate
def AuthoredSections(FeatureClasses: tuple[int, ...]) -> dict[str, bytes]:
    Bodies = EmptySectionPayloads()
    Bodies.update(NeutralEmptyPayloads())
    Bodies["FeatDefsIndex"] = FeatureIndexPayload(FeatureClasses)
    return Bodies


# two dozen sections only require their root struct name
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


# empty state sections are cheaper than modelling them
def MinimalSections() -> dict[str, bytes]:
    return {
        NameText: SectionValue(NameText, StructBegin(StructName) + CloseValue(1))
        for NameText, StructName in KMinimalStructs
    }


# the datum only part is the smallest model creo will load
def EmptyPartSections(FeatureClasses: tuple[int, ...]) -> dict[str, bytes]:
    Bodies = AuthoredSections(FeatureClasses)
    Bodies.update(MinimalSections())
    Bodies["BasBasData"] = DefaultBasBasData()
    Bodies["FeatDefsDtm"] = DefaultFeatDefsDtm(254.33012701892218)
    Bodies["AllFeatur"] = DefaultAllFeatur()
    return Bodies


# scalar values have three shorthand lanes worth using
def ScalarValue(Value: float) -> bytes:
    if Value == 0.0:
        return b"\x18"
    if Value == 1.0:
        return b"\x0f"
    if Value == -1.0:
        return b"\x10"
    return CompactDouble(Value)


# repeated scalars dominate the stream so runs need one owner
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
            Payload += b"\xe4"
        elif Extra == 2:
            Payload += b"\xe5"
        elif Extra == 3:
            Payload += b"\xe6"
        elif Extra > 3:
            Payload += b"\xe7" + IntValue(Extra)
        IndexValue += RunLength
    return Payload


# model identity lives here and nothing else may invent it
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
    Payload += StructHeader("tab_key_ptr") + b"\xf8\x42"
    Payload += StructHeader("cmprs_tabkey") + CloseValue(1)
    Payload += b"\xe1"
    Payload += b"\xe0\x01type\x00" + CloseValue(1) + IntValue(2)
    Payload += StructBegin("revnum_ptr")
    Payload += FieldValue(1, "geom_revnum", IntValue(GeomRevision))
    Payload += FieldValue(1, "cosm_revnum", IntValue(CosmRevision))
    Payload += b"\xe0\x01insert_layer_id\x00" + CloseValue(1) + b"\xf6"
    Payload += FieldValue(1, "layer_count", IntValue(LayerCount))
    Payload += FieldValue(2, "rel_part_eps", ScalarValue(RelativeEpsilon))
    Payload += FieldValue(2, "model_eps", ScalarValue(ModelEpsilon))
    Payload += FieldValue(1, "fixed_model_eps", IntValue(0))
    Payload += FieldValue(1, "part_type", IntValue(PartType))
    Payload += FieldValue(1, "first_ent_id", IntValue(FirstEntityId))
    Payload += FieldValue(2, "outline", b"\xf9\x02\x03" + RunValues(Outline))
    Payload += FieldValue(
        1, "attrib_array", b"\xf8" + IntValue(len(Attributes))
    ) + b"".join(IntValue(Value) for Value in Attributes)
    Payload += FieldValue(2, "max_part_size", ScalarValue(MaxPartSize))
    Payload += StructHeader("ref_part_tabs") + b"\xe3\xf2"
    return SectionValue("BasBasData", Payload)


# research needs a plausible default before callers supply real values
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


# a datum frame starts at identity in every trace we hold
KIdentityColumn = (1.0, 0.0, 0.0, 0.0)


# datum placement carries the fields the loader validates hardest
def DatumPlaneRecord(
    DatumId: int,
    Orient: int,
    Geometry2Id: int,
    Columns: tuple[tuple[float, ...], ...],
    Outline: tuple[float, ...],
    InstructionType: int = 515,
) -> bytes:
    Frame = tuple(Value for Column in Columns for Value in Column)
    Payload = b"\xe3"
    Payload += FieldValue(1, "id", IntValue(DatumId))
    Payload += FieldValue(1, "symbol_key", b"\xf6")
    Payload += FieldValue(1, "model_type", IntValue(2))
    Payload += NullStruct("group_info_ptr")
    Payload += StructBegin("place_rec_ptr")
    Payload += FieldValue(2, "local_sys", b"\xf9\x04\x03" + RunValues(Frame))
    Payload += FieldValue(1, "own_ref_id", b"\xf6")
    Payload += FieldValue(1, "orient", IntValue(Orient))
    Payload += FieldValue(0, "place_instruction_ptrs", b"\xf8\x01\xf7\x0b\xfb")
    Payload += b"\xe3"
    Payload += FieldValue(1, "type", IntValue(InstructionType))
    Payload += FieldValue(2, "offset", ScalarValue(0.0))
    Payload += FieldValue(1, "dim_id", b"\xf6")
    Payload += FieldValue(1, "ref_id", b"\xf6")
    Payload += FieldValue(1, "geometry1_id", b"\xf6")
    Payload += FieldValue(1, "geometry2_id", IntValue(Geometry2Id))
    Payload += FieldValue(1, "memb_num1", IntValue(0))
    Payload += FieldValue(1, "memb_num2", IntValue(0))
    Payload += FieldValue(1, "attr", b"\xf8\x03\xc0\x80\x00\x00\xe4")
    Payload += FieldValue(0, "plin_info_arr", b"\xf8\x02\xf7\x15\xfb")
    Payload += b"\xe3"
    Payload += FieldValue(1, "type", IntValue(1))
    Payload += StructBegin("data(plin_info_ref)")
    Payload += FieldValue(1, "id_type1", b"\xf5\x04")
    Payload += FieldValue(1, "id_type2", IntValue(5))
    Payload += FieldValue(2, "offset2", ScalarValue(0.0))
    Payload += b"\xf2"
    Payload += b"\xf7\x15\xe3" + IntValue(6)
    Payload += StructBegin("data(plin_info_ui_step)")
    Payload += FieldValue(1, "step_ids", b"\xf8\x01\xf5\x64")
    Payload += FieldValue(1, "attr", IntValue(0))
    Payload += FieldValue(2, "uv", b"\xf3\xf8\x02\x18\xe4")
    Payload += StructHeader("trf_arr") + b"\xf2"
    Payload += b"\xf8\x01\xf7\x1f\xfb"
    Payload += b"\xe3"
    Payload += FieldValue(1, "type", IntValue(11))
    Payload += FieldValue(1, "key", b"\xf6")
    Payload += FieldValue(1, "idx", IntValue(0))
    Payload += FieldValue(2, "transf", b"\xf9\x04\x03" + RunValues(Frame))
    Payload += StructHeader("plcm_revnum") + b"\xf2"
    Payload += b"\xe1"
    Payload += StructHeader("next_prop") + CloseValue(1)
    Payload += b"\xe1"
    Payload += FieldValue(1, "cond_tbl_idx", b"\xf6")
    Payload += FieldValue(10, "comment", b"\xe1")
    Payload += StructHeader("merge_info_ptr") + b"\xe1"
    Payload += FieldValue(1, "state_ind", b"\xf6")
    Payload += StructHeader("alumni_info") + b"\xe1"
    Payload += StructHeader("expl_state_ref") + b"\xe1"
    Payload += StructBegin("feat_outl_info")
    Payload += FieldValue(2, "ent_outl", b"\xf9\x02\x03" + RunValues(Outline))
    Payload += StructHeader("pre_roll_back") + b"\xe1"
    Payload += StructHeader("post_roll_back") + b"\xe1"
    Payload += StructHeader("post_regen") + b"\xe1"
    Payload += StructHeader("parchild_table") + CloseValue(1)
    Payload += b"\xe3"
    Payload += FieldValue(9, "Structure_Invalid", b"\xc0\xab\xcd")
    Payload += StructHeader("copy_info_ptr") + CloseValue(1)
    Payload += b"\xe1"
    Payload += StructHeader("embed_info_ptr") + b"\xe1"
    Payload += CloseValue(1)
    return Payload


# redeclaring fields mid array shifts every later index
def DatumPlaneReplay(
    DatumId: int,
    Orient: int,
    Geometry2Id: int,
    Columns: tuple[tuple[float, ...], ...],
    Outline: tuple[float, ...],
    InstructionType: int,
    Lead: bytes = b"\xf7\x02",
) -> bytes:
    Frame = tuple(Value for Column in Columns for Value in Column)
    Payload = Lead + b"\xe3"
    Payload += IntValue(DatumId)
    Payload += b"\xf6"
    Payload += IntValue(2)
    Payload += b"\xe1\xe3"
    Payload += RunValues(Frame)
    Payload += b"\xf6"
    Payload += IntValue(Orient)
    Payload += b"\xf8\x01\xf7\x0b\xfb\xe3"
    Payload += b"\xf7\x0c" + IntValue(InstructionType)
    Payload += ScalarValue(0.0)
    Payload += b"\xf6\xf6\xf6"
    Payload += IntValue(Geometry2Id)
    Payload += b"\x00\x00"
    Payload += b"\xc0\x80\x00\x00\xe4"
    Payload += b"\xf8\x02\xf7\x15\xfb\xe3"
    Payload += b"\xf7\x16" + IntValue(1)
    Payload += b"\xf7\x17\xe3\xf5\x04"
    Payload += IntValue(5)
    Payload += ScalarValue(0.0)
    Payload += b"\xe3" + IntValue(6)
    Payload += b"\xf7\x1b\xe3\xf5\x64\x00"
    Payload += ScalarValue(0.0)
    Payload += b"\xe4"
    Payload += b"\xf8\x01\xf7\x1f\xfb\xe3"
    Payload += b"\xf7\x20" + IntValue(11)
    Payload += b"\xf6" + IntValue(0)
    Payload += RunValues(Frame)
    Payload += b"\xe1\xe1\xf6\xe1\xe1\xf6\xe1\xe1\xe3"
    Payload += RunValues(Outline)
    Payload += b"\xe1\xe1\xe1\xe3\xc0\xab\xcd\xe1\xe1"
    return Payload


# the coordinate system record is last so it may declare fields
def CsysReplay(
    CsysId: int, Columns: tuple[tuple[float, ...], ...], Outline: tuple[float, ...]
) -> bytes:
    Frame = tuple(Value for Column in Columns for Value in Column)
    Payload = b"\xe0\x00feat_defs_979\x00\xf2\xf8\x01\xf7\x35\xfb\xe3"
    Payload += b"\xf7\x03" + IntValue(CsysId)
    Payload += b"\xf6" + IntValue(2) + b"\xe1\xe3"
    Payload += RunValues(Frame)
    Payload += b"\xf6" + IntValue(0)
    Payload += b"\xf8\x07\xf7\x0b\xfb\xe3"
    Payload += b"\xf7\x0c\x84\xd8" + ScalarValue(0.0)
    Payload += b"\xf6\xf6" + IntValue(6) + b"\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x02\xf7\x15\xfb\xe3"
    Payload += b"\xf7\x16\x35"
    Payload += b"\xe0\x00data(plin_info_ref_uv)\x00\xe3"
    Payload += b"\xe0\x02uv_val\x00\xf8\x02\x18\xe4\xf2"
    Payload += b"\xf7\x15\xe3" + IntValue(6)
    Payload += b"\xf7\x1b\xe3\xf5\x64\x00\x18\xe4\xf1"
    Payload += b"\xf7\x0b\xe3\x84\xd8\x18\xf6\xf6"
    Payload += IntValue(8) + b"\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x02\xf7\x15\xfb\xe3\xf7\x16\x35\xf7\x36\xe3\x18\xe4"
    Payload += b"\xe3" + IntValue(6)
    Payload += b"\xf7\x1b\xe3\xf5\x64\x00\x18\xe4"
    Payload += b"\xe3\x84\xd8\x18\xf6\xf6" + IntValue(4) + b"\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x02\xf7\x15\xfb\xe3\xf7\x16\x35\xf7\x36\xe3\x18\xe4"
    Payload += b"\xe3" + IntValue(6)
    Payload += b"\xf7\x1b\xe3\xf5\x64\x00\x18\xe4"
    Payload += b"\xe3\x9d\x4c\x18\xf6\xf6" + IntValue(6) + b"\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x01\xf7\x15\xfb\xe3\xf7\x16" + IntValue(6)
    Payload += b"\xe3\xf5\x64\x00\x18\xe4"
    Payload += b"\xe3\x84\xf6\x2f\x08\x00\xf6\xf6\xf6\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x01\xf7\x15\xfb\xe3\xf7\x16" + IntValue(6)
    Payload += b"\xe3\xf5\x64\x00\x18\xe4"
    Payload += b"\xe3\x84\xf7\x48\x00\x00\xf6\xf6\xf6\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x01\xf7\x15\xfb\xe3\xf7\x16" + IntValue(6)
    Payload += b"\xe3\xf5\x64\x00\x18\xe4"
    Payload += b"\xe3\x9d\x55\x18\xf6\xf6" + IntValue(8) + b"\xf6\x00\x00\x00\xe5"
    Payload += b"\xf8\x01\xf7\x15\xfb\xe3\xf7\x16" + IntValue(6)
    Payload += b"\xe3\xf5\x64\x00\x18\xe4\xf2"
    Payload += b"\xf7\x1f\xf8\x01\xf7\x1f\xfb\xe3\xf7\x20" + IntValue(10)
    Payload += b"\xf6" + IntValue(0)
    Payload += RunValues(Frame)
    Payload += b"\xe1\xe1\xf6\xe1\xe1\xf6\xe1\xe1\xe3"
    Payload += RunValues(Outline)
    Payload += b"\xe1\xe1\xe1\xe3\xc0\xab\xcd\xe1\xe1\xf3"
    return Payload


# the datum section is assembled from records plus one csys
def FeatDefsDtmPayload(
    Planes: tuple[
        tuple[int, int, int, tuple[tuple[float, ...], ...], tuple[float, ...], int], ...
    ],
    CsysId: int,
    CsysColumns: tuple[tuple[float, ...], ...],
    CsysOutline: tuple[float, ...],
) -> bytes:
    Payload = StructBegin("Sld_FeatDefsDtm")
    Payload += FieldValue(
        0,
        "feat_defs_923",
        b"\xf8" + IntValue(len(Planes)) + b"\xf7\x02\xfb",
    )
    for IndexValue, Plane in enumerate(Planes):
        DatumId, Orient, Geometry2Id, Columns, Outline, InstructionType = Plane
        if IndexValue == 0:
            Payload += DatumPlaneRecord(
                DatumId, Orient, Geometry2Id, Columns, Outline, InstructionType
            )
        else:
            Payload += DatumPlaneReplay(
                DatumId,
                Orient,
                Geometry2Id,
                Columns,
                Outline,
                InstructionType,
                b"\xf7\x02" if IndexValue == 1 else b"",
            )
    Payload += CsysReplay(CsysId, CsysColumns, CsysOutline)
    return SectionValue("FeatDefsDtm", Payload)


# callers need a complete datum section before parameters exist
def DefaultFeatDefsDtm(Extent: float) -> bytes:
    First = ((1.0, 0.0, 0.0, 0.0),) * 3
    Second = (
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 1.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 0.0),
    )
    Third = (
        (0.0, 0.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 1.0),
        (0.0, 0.0, 0.0, 0.0),
    )
    Front = (Extent, Extent, 0.0, -Extent, -Extent, 0.0)
    Top = (Extent, 0.0, Extent, -Extent, 0.0, -Extent)
    Right = (0.0, Extent, Extent, 0.0, -Extent, -Extent)
    Csys = (
        (1.0, 0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, -1.0, 0.0, 0.0),
        (0.0, 0.0),
    )
    return FeatDefsDtmPayload(
        (
            (7, 1, 8, First, Front, 515),
            (5, 1, 6, Second, Top, 514),
            (3, 1, 4, Third, Right, 513),
        ),
        11,
        Csys,
        (0.0,) * 6,
    )


# a part with no surfaces still needs the section present
def EmptyVisibGeom() -> bytes:
    return SectionValue(
        "VisibGeom",
        StructBegin("Sld_VisGeom") + StructHeader("active_geom") + b"\xe2\xf2",
    )


# the generated container is the only end to end authoring test
def EmptyPartContainer(
    FeatureClasses: tuple[int, ...] = (923, 979, 917),
    ModelName: str = "part.prt",
) -> bytes:
    Bodies = EmptyPartSections(FeatureClasses)
    Bodies["VisibGeom"] = EmptyVisibGeom()
    return BuildContainer(tuple(Bodies.items()), ModelName)


# compact widths keep stored arrays small and aligned
def CompactInt(Value: int) -> bytes:
    if Value < 0:
        raise ValueError("CompactInt takes a non-negative value")
    if Value <= 0x7F:
        return bytes((Value,))
    if Value <= 0x3FFF:
        return bytes((0x80 | (Value >> 8), Value & 0xFF))
    if Value <= 0x1FFFFF:
        return bytes((0xC0 | (Value >> 16), (Value >> 8) & 0xFF, Value & 0xFF))
    Width = max(1, (Value.bit_length() + 7) // 8)
    return bytes((0xE7 + Width,)) + Value.to_bytes(Width, "big")


# negative sentinels appear constantly so one encoder owns them
def SignedInt(Value: int) -> bytes:
    if Value == -1:
        return b"\xf6"
    if Value < 0:
        return b"\xf5" + CompactInt(-Value)
    return CompactInt(Value)


# count and elements must agree or the reader desynchronises
def SignedIntArray(Values: tuple[int, ...]) -> bytes:
    Payload = b"\xf8" + CompactInt(len(Values))
    IndexValue = 0
    while IndexValue < len(Values):
        RunLength = 1
        while (
            IndexValue + RunLength < len(Values)
            and Values[IndexValue + RunLength] == Values[IndexValue]
        ):
            RunLength += 1
        Payload += SignedInt(Values[IndexValue])
        Extra = RunLength - 1
        if Extra == 1:
            Payload += b"\xe4"
        elif Extra == 2:
            Payload += b"\xe5"
        elif Extra == 3:
            Payload += b"\xe6"
        elif Extra > 3:
            Payload += b"\xe7" + CompactInt(Extra)
        IndexValue += RunLength
    return Payload


# replay lanes omit the count the first lane already declared
def SignedIntElements(Values: tuple[int, ...]) -> bytes:
    Body = SignedIntArray(Values)
    Count = len(b"\xf8" + CompactInt(len(Values)))
    return Body[Count:]


# the mask lane is a closed array behind a close token
def FlagValue(Values: tuple[int, ...]) -> bytes:
    return b"\xf1" + SignedIntArray(Values)


# one clean slot satisfies the loader and carries no vendor state
KCleanFlagSlots = 1


# the mask field only has to be a well formed non empty array
def CleanFlagValue() -> bytes:
    return FlagValue((-1,) * KCleanFlagSlots)


# replay records carry the elements without the count the first one declared
def CleanFlagElements() -> bytes:
    return SignedIntElements((-1,) * KCleanFlagSlots)


# the datum record is the only feature shape creo accepts without geometry
def DatumFeatureRecord(
    FeatureId: int,
    FeatureClass: int,
    SectionName: str,
    FirstGeomId: int,
    BodyId: int,
    MaskValues: tuple[int, ...],
    CreateDate: int,
    RegenDate: int,
    StampTime: int,
    RandomNum: int,
    HostId: int,
    RevNum: int,
    NumPlins: int,
    LargestPrevRev: int,
    ExtraSchema: bool = False,
) -> bytes:
    Payload = FieldValue(1, "id", SignedInt(FeatureId))
    Payload += FieldValue(1, "indep_attributes_arr", SignedIntArray((4097, 0, 0, 0)))
    Payload += StructHeader("feat_type_ptr") + b"\xe3"
    Payload += FieldValue(1, "table_id", SignedInt(-1))
    Payload += FieldValue(1, "type", SignedInt(FeatureClass))
    Payload += FieldValue(10, "feattype_key", b"\xe1")
    Payload += FieldValue(1, "form", SignedInt(0))
    Payload += FieldValue(1, "attributes", SignedIntArray((0,) * 8 + (16, 0, 0)))
    Payload += FieldValue(1, "placement", SignedInt(0))
    Payload += FieldValue(1, "intersection", SignedInt(-1))
    Payload += FieldValue(1, "internal_udf_type", SignedInt(-1))
    Payload += StructHeader("param_choice_ptr") + b"\xe3"
    Payload += FieldValue(1, "blend_choice", SignedInt(0))
    Payload += FieldValue(1, "depth_choice", SignedInt(0))
    Payload += FieldValue(1, "angle_choice", SignedInt(0))
    Payload += FieldValue(1, "pat_choice", SignedInt(-1))
    Payload += FieldValue(1, "round_choice", SignedInt(-1))
    Payload += FieldValue(1, "subsec_choice", SignedInt(-1))
    Payload += FieldValue(1, "sweep_choice", SignedInt(0))
    Payload += FieldValue(1, "dome_choice", SignedInt(0))
    Payload += FieldValue(1, "draft_choice", SignedInt(0))
    Payload += FieldValue(1, "misc_choice", SignedIntArray((0,) * 6))
    Payload += FieldValue(1, "assoc_type", b"\xf1" + SignedInt(0))
    Payload += FieldValue(1, "comp_like_type", SignedInt(-1))
    Payload += FieldValue(
        10, "sect_name", b"\xf1" + SectionName.encode("latin-1") + b"\x00"
    )
    Payload += StructHeader("idtab_ptr") + b"\xe3"
    Payload += FieldValue(0, "srf_id_tab_ptr", b"\xf8\x01\xf7\x1d\xfb")
    Payload += b"\xe3"
    Payload += FieldValue(1, "fc_hist", SignedIntArray((FirstGeomId, 0, 0, 0)))
    Payload += StructHeader("save_geoms") + b"\xf2\xe3"
    Payload += FieldValue(
        2, "transform", b"\xf9\x04\x03" + RunValues(KIdentityColumn * 3)
    )
    Payload += FieldValue(1, "cr_flags_xar", FlagValue(MaskValues))
    Payload += StructHeader("cvt_feat_dat") + b"\xe1"
    Payload += StructHeader("feat_dates_ptr") + b"\xe3"
    Payload += FieldValue(1, "creat_date", SignedInt(CreateDate))
    Payload += FieldValue(1, "regen_date", SignedInt(RegenDate))
    Payload += StructHeader("intrs_pairs_ptr") + b"\xf2\xe3"
    Payload += FieldValue(1, "first_geom_id", b"\xf1" + SignedInt(FirstGeomId))
    Payload += StructHeader("topology_increment") + b"\xe3"
    Payload += StructHeader("body_geom_hdr") + b"\xe2"
    Payload += FieldValue(0, "h_body_geom", b"\xf8\x01\xf7\x2a\xfb")
    Payload += b"\xe2"
    Payload += FieldValue(1, "p_body", SignedInt(BodyId))
    Payload += FieldValue(1, "first_geom", SignedInt(0))
    Payload += FieldValue(1, "body_id", SignedInt(BodyId))
    Payload += FieldValue(1, "first_geom_id", SignedInt(-1))
    Payload += FieldValue(1, "ids_null_goem", b"\xf2" + SignedIntArray((BodyId,)))
    Payload += FieldValue(1, "first_quilt", b"\xf1" + SignedInt(0))
    Payload += FieldValue(1, "first_lo", SignedInt(0))
    Payload += FieldValue(1, "first_hybrid_body", SignedInt(0))
    Payload += FieldValue(2, "outline", b"\xf9\x02\x03\x18\xe7\x05")
    Payload += FieldValue(2, "max_part_size", b"\x18")
    Payload += FieldValue(2, "cur_max_size", b"\x18")
    Payload += StructHeader("xform_increment") + b"\xe1"
    Payload += FieldValue(1, "roll_back_id", SignedInt(-1))
    Payload += StructHeader("time_stamp") + b"\xe3"
    Payload += FieldValue(1, "time", SignedInt(StampTime))
    Payload += FieldValue(1, "random_num", SignedInt(RandomNum))
    Payload += FieldValue(1, "hostid", SignedInt(HostId))
    Payload += StructHeader("quilt_diff") + b"\xf1\xe1"
    Payload += StructHeader("body_diff") + b"\xe1"
    Payload += StructHeader("hybrid_body_diff") + b"\xe1"
    Payload += StructHeader("lo_diff") + b"\xe1"
    Payload += FieldValue(1, "attributes", SignedInt(32769))
    Payload += StructHeader("objs_affected") + b"\xe1"
    Payload += StructHeader("SpecTopolRefs") + b"\xe1"
    Payload += StructHeader("ActiveTopolRefs") + b"\xe1"
    Payload += FieldValue(1, "revnum", b"\xf1" + SignedInt(RevNum))
    Payload += StructHeader("rev_rec") + b"\xe3"
    Payload += StructHeader("extnd_rev_tab") + b"\xe1"
    Payload += FieldValue(1, "num_plins", SignedInt(NumPlins))
    Payload += FieldValue(1, "largest_prev_rev", SignedInt(LargestPrevRev))
    Payload += FieldValue(1, "largest_prev_rev_delta", SignedInt(0))
    Payload += StructHeader("revnum_cache_data") + b"\xe1"
    Payload += FieldValue(1, "rev_flags", SignedInt(0))
    return Payload


# reference arrays keep their count so replay scanning must see real tokens
def HasReferenceToken(Value: bytes) -> bool:
    Index = 1
    while Index < len(Value):
        Token = Value[Index]
        if Token == 0xF7:
            return True
        if Token == 0xF6 or Token <= 0x7F:
            Index += 1
        elif Token == 0xF5:
            Index += 2
        elif Token <= 0xBF:
            Index += 2
        elif Token <= 0xDF:
            Index += 3
        elif 0xE8 <= Token <= 0xEB:
            Index += 1 + (Token - 0xE7)
        else:
            Index += 1
    return False


# replays repeat the first record positionally so no field may be redeclared
def ReplayOf(Definition: bytes) -> bytes:
    Parser = StreamParser(Definition)
    Spans: list[tuple[str, bytes]] = []
    Original = Parser.ReadField

    # capturing spans is how the replay keeps the definition order
    def ReadField(Descriptor) -> object:
        Start = Parser.Reader.Position
        Node = Original(Descriptor)
        Spans.append((Descriptor.name, Definition[Start : Parser.Reader.Position]))
        return Node

    Parser.ReadField = ReadField
    Parser.Run()
    Payload = b""
    Seen: set[str] = set()
    for Position, (NameText, Value) in enumerate(Spans, start=1):
        if NameText in Seen:
            Payload += b"\xf7" + CompactInt(Position)
        Seen.add(NameText)
        if Value[:1] in (b"\xf1", b"\xf2"):
            Value = Value[1:]
        if Value[:1] == b"\xf8" and not HasReferenceToken(Value):
            Marker = Value[1]
            Width = (
                1
                if Marker <= 0x7F
                else (
                    2
                    if Marker <= 0xBF
                    else 3 if Marker <= 0xDF else 1 + (Marker - 0xE7)
                )
            )
            Value = Value[1 + Width :]
        if Value[:1] in (b"\xf9",):
            Value = Value[3:]
        Payload += Value
    return Payload


# the loader wants four layer entries regardless of how many features exist
KLayerEntries = 4


# layer entries carry feature ids the loader does not check against the list
def LayerListTail(FeatureId: int) -> bytes:
    Payload = FieldValue(
        0,
        "layer_list",
        b"\xf8" + CompactInt(KLayerEntries) + b"\xf7\x51\xfb",
    )
    for IndexValue in range(KLayerEntries):
        First = IndexValue == 0
        Payload += b"" if First else b"\xf7\x51"
        Payload += b"\xe2"
        if First:
            Payload += b"\xe0\x01feat_id\x00"
        Payload += SignedInt(FeatureId)
        if First:
            Payload += b"\xe0\x01layer_id\x00"
        Payload += SignedInt(0)
        if First:
            Payload += b"\xe0\x01back_layer_id\x00"
        Payload += SignedInt(0)
        if First:
            Payload += b"\xf1"
    Payload += StructHeader("footer") + b"\xf2\xe3"
    Payload += StructHeader("foot_first_feat_ptr") + b"\xe1"
    Payload += FieldValue(1, "foot_layer_count", SignedInt(0))
    Payload += b"\xf2"
    return Payload


# a single feature needs no replay records and therefore no schema mask vector
def AllFeaturPayload(Record: bytes, FeatureId: int) -> bytes:
    Payload = StructHeader("Sld_Features") + b"\xe3"
    Payload += StructHeader("first_feat_ptr") + b"\xe3"
    Payload += Record
    Payload += StructHeader("next_feat_ptr") + b"\xe1"
    Payload += LayerListTail(FeatureId)
    return SectionValue("AllFeatur", Payload)


# a datum only part needs one feature record and no replay records
def DefaultAllFeatur() -> bytes:
    Record = DatumFeatureRecord(
        7,
        923,
        "FRONT",
        8,
        -5778,
        (-1,) * 252,
        200000,
        200001,
        1000000000,
        12345,
        99,
        3,
        1,
        3,
    )
    return AllFeaturPayload(Record, 7)
