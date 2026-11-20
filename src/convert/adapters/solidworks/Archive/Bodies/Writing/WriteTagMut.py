from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag


# structural tags must use the shared native reference grammar in every body stream
def WriteTagMut(WriterValue: BodyWriter, TagValue: ArchiveTag) -> None:
    WriterValue.OutputValue.extend(EncodeTag(TagValue))
