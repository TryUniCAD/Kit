from convert.formats.Fusion.BrepCodec.Attributes.GenericPrefix import MakeTagPrefix
from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeFeatureTag(Owner: int, TagValue: FeatureTag) -> GeometryRecord:
    Payload = (
        *MakeTagPrefix(),
        TagValue.Selector,
        CountedText(TagValue.Label),
        0,
        len(TagValue.Operations),
        *TagValue.Operations,
        0,
    )
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload)
