from pathlib import Path as FilePath

from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from tests.Convert.Solidworks.Properties.ChangeTextCmgr import ChangeTextCmgr
from tests.Convert.Solidworks.Properties.ChangeTextXml import ChangeTextXml


# every negative keeps an actual readable geometry archive and changes only its declared optional property boundary
def ChangeTextPart(SourcePath: FilePath, FaultValue: str) -> FilePath:
    Archive = SldprtArchive.OpenAction(SourcePath)
    StreamsValue = Archive.streams
    if FaultValue == "stale-id":
        StreamsValue["docProps/Config-19-Properties.xml"] = StreamsValue.pop(
            "docProps/Config-0-Properties.xml"
        )
    elif FaultValue in ("stale-owner", "stale-cache"):
        StreamsValue["Contents/CMgr"] = ChangeTextCmgr(
            StreamsValue["Contents/CMgr"], FaultValue == "stale-owner"
        )
    elif FaultValue == "malformed":
        StreamsValue["docProps/custom.xml"] = b"<Properties>"
    elif FaultValue in ("doctype", "utf16-doctype"):
        TextValue = '<!DOCTYPE Properties [<!ENTITY text "unqualified">]><Properties>&text;</Properties>'
        StreamsValue["docProps/custom.xml"] = TextValue.encode(
            "utf-16" if FaultValue == "utf16-doctype" else "utf-8"
        )
    elif FaultValue == "advanced-manager":
        StreamsValue["Contents/CusProps"] = b"unclassified advanced property owner"
    else:
        StreamsValue["docProps/custom.xml"] = ChangeTextXml(
            StreamsValue["docProps/custom.xml"], FaultValue
        )
    TargetPath = SourcePath.with_stem(SourcePath.stem + "-" + FaultValue)
    _ = TargetPath.write_bytes(BuildSldprt(StreamsValue, FormatVersion=4))
    return TargetPath
