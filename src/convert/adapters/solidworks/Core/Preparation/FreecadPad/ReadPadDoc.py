from collections.abc import Mapping

from convert.adapters.freecad.Native import LoadNative, NativeMeta, NativeSource
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument


# saved presentation must agree with the actual document and all retained object owners
def ReadPadDoc(Document: CadDocument) -> Mapping[str, object]:
    Source = Document.source
    PairValue = NativeDocPair(Document)
    if (
        Source.format_id != "freecad.fcstd"
        or Source.container_version != "1"
        or Source.attributes != {"freecad_schema_version": "4"}
        or PairValue is None
        or PairValue[0].data is None
        or PairValue[0].sha256 != Source.sha256
    ):
        raise ValueError("FreeCAD Pad text requires the intact document binding")
    DataValue = PairValue[0].data
    ArchiveValue = LoadNative(DataValue)
    Metadata = NativeRecord(Document.metadata.get("freecad"))
    if NativeSource(
        DataValue, Source.path, ArchiveValue
    ) != Source or Metadata != NativeMeta(ArchiveValue, None, {}):
        raise ValueError("FreeCAD Pad text disagrees with its actual saved owner")
    return Metadata
