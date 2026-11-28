from pathlib import Path as FilePath
from xml.etree.ElementTree import SubElement, tostring as EncodeXml

from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    build_sldprt as BuildArchive,
)
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml


# captions and negative identifiers must not impersonate typed owner membership when preserving authored metadata
def AddUnknownRow(InputPath: FilePath, KindValue: str, NativeId: int) -> FilePath:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    Streams = dict(Archive.streams)
    Keywords = Archive.require(KeywordsStream)
    RootValue = ParseXml(Keywords)
    _ = SubElement(
        RootValue,
        "Feature",
        {"id": str(NativeId), "Name": "authored preserved row", "Type": KindValue},
    )
    Streams[KeywordsStream] = Keywords[: Keywords.index(b"<")] + EncodeXml(
        RootValue, encoding="utf-8", xml_declaration=True
    )
    OutputPath = InputPath.with_stem(f"AuthoredTree{NativeId}")
    with OutputPath.open("xb") as Output:
        _ = Output.write(BuildArchive(Streams))
    return OutputPath
