from convert.formats.Fusion.BrepCodec.Attributes.GenericPrefix import MakeTagPrefix
from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeBodyTag(Owner: int, Identity: BodyIdentity, PriorLink: int) -> GeometryRecord:
    Payload = (
        *MakeTagPrefix(),
        3,
        CountedText(str(Identity.OperationId)),
        Identity.GenerationRef,
        0,
        0,
    )
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload, PriorLink=PriorLink)
