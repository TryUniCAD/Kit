from hashlib import sha256 as CalcSha

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import PrepareImport
from convert.adapters.solidworks.Core.Writing.Imports.ImportResult import ImportResult
from convert.adapters.solidworks.Core.Writing.Imports.ImportTarget import ImportTarget
from convert.adapters.solidworks.Core.Writing.Imports.ReadImportMeas import ReadImportMeas
from interchange.document.Models.DocumentModel import CadDocument


# every published native byte must be regenerated before the output is opened
def EmitImportMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckPartOpts(OptionsValue)
    Measurement = ReadImportMeas(SettingsValue)
    OutputPath, SettingsValue = ImportTarget(TargetValue, SettingsValue)
    Payload = PrepareImport(
        DocumentValue, OutputPath or TargetValue, Measurement.EpochValue, SettingsValue
    ).BytesValue
    if len(Payload) != Measurement.SizeValue or CalcSha(Payload).hexdigest() != Measurement.CandidateSha:
        raise ValueError("regenerated local solid has no exact native measurement")
    if OutputPath is None:
        WriteWholeMut(TargetValue, Payload)
    else:
        with OutputPath.open("wb" if SettingsValue.overwrite else "xb") as OutputFile:
            if OutputFile.write(Payload) != len(Payload):
                raise OSError("short native local solid write")
    return ImportResult(OutputPath, Measurement)
