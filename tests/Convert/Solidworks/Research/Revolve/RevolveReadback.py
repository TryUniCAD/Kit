from __future__ import annotations

from struct import unpack as UnpackValues
from typing import cast as CastValue

from convert.adapters.base.SafeParsing import ParseUntrusted
from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.Composition.NodeFields import ReadFields
from tests.Convert.Solidworks.Research.Composition.ProfileRoots import ReadLinkedRoots


# verify stored profile ownership numeric input and xml by decoding the generated file
def ReadRevolution(ArchiveFile: SldprtArchive, CodecReg: object) -> dict[str, object]:
    _, Roots = ReadLinkedRoots(ArchiveFile, CodecReg)
    Native = next(
        RootNode
        for RootNode in Roots
        if getattr(RootNode, "cls", None) == "moRevolution_c"
    )
    Profile = next(
        RootNode
        for RootNode in Roots
        if getattr(RootNode, "cls", None) == "moProfileFeature_c"
    )
    NativeFields, ProfileFields = ReadFields(Native), ReadFields(Profile)
    FeatureRefs = CastValue(
        dict[str, dict[str, list[dict[str, object]]]], NativeFields["f60"]
    )
    AxisFields = ReadFields(NativeFields["f830"])
    Selected = ReadFields(AxisFields["f58"])
    LineId = CastValue(int, ReadFields(Selected["f0f8"])["idx"])
    LineRows = CastValue(
        list[dict[str, object]], ReadFields(ProfileFields["pd_f80"])["lines"]
    )
    AxisRow = LineRows[LineId]
    AxisEntity = CastValue(dict[str, object], AxisRow["line"])
    EndFields = ReadFields(NativeFields["f8d8"])
    Display = ReadFields(EndFields["f18"])
    Handle = ReadFields(CastValue(list[dict[str, object]], Display["f850"])[0]["o"])
    Parameter = ReadFields(ReadFields(Handle["ff0"])["f28"])
    CachedValue = CastValue(dict[str, bytes], Display["f5b0"])["data"]
    Keywords = ArchiveFile.require("swXmlContents/KeyWords")
    XmlRoot = ParseUntrusted(Keywords[1:])
    KeywordFeature = next(
        Element for Element in XmlRoot if Element.get("Type") == "Revolve"
    )
    KeywordSketch = next(
        Element for Element in XmlRoot if Element.get("id") == str(ProfileFields["f08"])
    )
    KeywordDimension = next(
        Element for Element in KeywordFeature if Element.tag == "Dimension"
    )
    return {
        "revolution": {
            "angle_rad": Parameter["f58"],
            "cached_angle_rad": UnpackValues("<d", CachedValue)[0],
            "mode": NativeFields["f820"],
            "reverse": NativeFields["f824"],
            "single_end": EndFields["f08"],
            "end_condition": EndFields["f0c"],
            "profile_owned": FeatureRefs["list"]["items"][0]["o"] is Profile,
            "profile_reference_id": CastValue(dict[str, object], Selected["ff0"])[
                "f00"
            ],
            "profile_id": ProfileFields["f08"],
            "selected_line_id": LineId,
            "axis_mark": Selected["f100"],
            "line_mark": AxisEntity["f08"],
            "axis_record_flags": AxisRow["flags"],
            "axis_entity_flags": AxisEntity["f54"],
            "axis_start": AxisFields["fc8"],
            "axis_direction": AxisFields["fe0"],
            "axis_length": AxisFields["fb8"],
            "legacy_displays_absent": NativeFields["f808"]
            is NativeFields["f810"]
            is None,
            "reverse_display_absent": EndFields["f20"] is None,
            "converted_displays": ReadFields(NativeFields["f818"])["n"],
            "keyword_angle": KeywordDimension.text,
            "keyword_axis_profile": KeywordSketch.attrib,
            "keyword_feature_id": int(KeywordFeature.attrib["id"]),
            "feature_id": NativeFields["f08"],
            "keyword_frame": Keywords[0] == 0x86
            and Keywords.endswith(b"\r\n")
            and b" />" not in Keywords,
        },
    }
