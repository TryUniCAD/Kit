from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Config.DescribeConfig import DescribeConfig
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph


# public compatibility reads need exact grammar evidence while retaining their previous semantic path
def ReadConfigInfo(
    BufferValue: bytes,
    HeaderBuffer: bytes,
    VersionValue: int | None,
    ManagerInfo: Mapping[str, object],
) -> Mapping[str, object]:
    UsageValue = BodyUsage()
    try:
        if VersionValue is None:
            raise ValueError("SOLIDWORKS configuration archive version is unavailable")
        HeaderValue = ReadHeaderGraph(HeaderBuffer, VersionValue)
        GraphValue = ReadConfigMut(
            BufferValue, VersionValue, HeaderValue, UsageValue=UsageValue
        )
        return DescribeConfig(GraphValue, ManagerInfo)
    except (TypeError, ValueError, KeyError) as ErrorInfo:
        return {
            "status": "unsupported",
            "archive_version": VersionValue,
            "diagnostic": str(ErrorInfo),
            "usage": GetBodyReport(UsageValue),
            "full_linked_graph": False,
            "resolved_body_codec_promoted": False,
        }
