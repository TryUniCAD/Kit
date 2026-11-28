from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import (
    BuildSweepPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ColdSwSource import (
    KColdSweepSource,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ReadColdIntent import (
    ReadColdIntent,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwDoc import MakeSwDesign
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import (
    ReadSwGraph,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordSource import CadSource


# a complete independently rebuilt archive is required before projecting cache free sweep geometry
def ReadColdSw(
    Archive: SldprtArchive, DataValue: bytes, Label: str, IncludeBrep: bool
) -> CadDocument:
    try:
        GraphValue = ReadSwGraph(Archive, ColdSweep=True)
        IntentValue = ReadColdIntent(GraphValue)
        if BuildSweepPart(IntentValue).BytesValue != DataValue:
            raise ValueError("canonical sweep reconstruction differs from source")
        SourceValue = CadSource(
            KPartFormatId,
            Label,
            CalcSha(DataValue).hexdigest(),
            container_version="4",
            attributes={
                KColdSweepSource: True,
                "native_locator": IntentValue.OutputValue.PathName,
                "written_at": IntentValue.OutputValue.SavedAt,
            },
        )
        Document = MakeSwDesign(
            GraphValue, SourceValue, IntentValue.NameValue, IncludeBrep, SavedBody=None
        )
        Document.assert_valid()
        return Document
    except (IndexError, KeyError, TypeError, ValueError, SyntaxError) as ErrorValue:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS cold sweep: {ErrorValue}"
        ) from ErrorValue
