from pathlib import Path as FilePath
from xml.etree.ElementTree import tostring as EncodeXml

from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    build_sldprt as BuildArchive,
)
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Container.Format import KeywordsStream


# cached keyword text must not override retained typed names live parameters or profile ownership
def StaleKeywords(InputPath: FilePath) -> FilePath:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    Streams = dict(Archive.streams)
    Keywords = Archive.require(KeywordsStream)
    RootValue = ParseXml(Keywords)
    (BossValue,) = tuple(RootValue.iter("Extrusion"))
    PlaneValue = next(
        NodeValue for NodeValue in RootValue if NodeValue.get("Name") == "Front Plane"
    )
    BossValue.set("Name", "Stale cached feature name")
    BossValue.set("DissectableChildren", str(PlaneValue.get("id")))
    (Dimension,) = tuple(BossValue.iter("Dimension"))
    setattr(Dimension, "text", "173.625")
    Streams[KeywordsStream] = Keywords[: Keywords.index(b"<")] + EncodeXml(
        RootValue, encoding="utf-8", xml_declaration=True
    )
    OutputPath = InputPath.with_stem("StaleKeywordChild")
    with OutputPath.open("xb") as Output:
        _ = Output.write(BuildArchive(Streams))
    return OutputPath
