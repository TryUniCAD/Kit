from hashlib import sha256 as CalcSha

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PrepareOffPart import (
    PrepareOffPart,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.OffsetOutput import (
    OffsetOutput,
)
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.OffsetOptions import (
    ReadOffOptions,
)
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.ReadOffReport import (
    ReadOffReport,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# complete regeneration is required before either a file or caller owned stream receives measured output
def EmitOffsetMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(OptionsValue)
    ReportHash, AcceptedHashes = ReadOffReport(Receipt)
    InputValue, Settings = ReadOffOptions(Settings)
    RecipeValue = InputValue.RecipeValue
    OutputPath, BuildSettings = OffsetOutput(
        TargetValue, Settings, RecipeValue.OutputValue.PathName
    )
    Payload = PrepareOffPart(
        DocumentValue,
        OutputPath or TargetValue,
        WrittenAt,
        BuildSettings,
        RecipeValue=RecipeValue,
        TextPoint=InputValue.RadialTextPoint,
    ).BytesValue
    Digest = CalcSha(Payload).hexdigest()
    if Digest not in AcceptedHashes:
        raise ValueError(
            "regenerated SOLIDWORKS offset part has no matching native measurement"
        )
    Evidence = FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "oracle_build": KOraclePart["build"],
                    "native_report_sha256": ReportHash,
                    "generated_sha256": Digest,
                }
            )
        }
    )
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, BuildSettings, Payload, Evidence, Transfers
    )
