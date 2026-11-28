from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.NestMeasure import (
    NestMeasure,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.NestProofPins import (
    KNestProofPins,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# caller evidence selects an authenticated whole hierarchy and cannot supply its own passing verdict
def ReadNestMeas(OptionsValue: WriteOptions) -> NestMeasure:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "SOLIDWORKS nested publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    EpochValue = Envelope.get("written_at")
    if (
        Envelope.keys() != {"written_at", "receipt"}
        or type(EpochValue) is not int
        or not 0 < EpochValue <= 0xFFFFFFFF
    ):
        raise ValueError("nested measurement requires its exact creation epoch")
    Receipt = ReadMeasMap(Envelope["receipt"])
    if (
        Receipt.keys()
        != {"schema", "generated_manifest_sha256", "native_result_sha256"}
        or Receipt.get("schema") != "kit.sw2026.rigid-nested-bundle-evidence.v1"
    ):
        raise ValueError("nested measurement requires a supported bundle receipt")
    ManifestSha = ReadMeasSha(Receipt.get("generated_manifest_sha256"))
    ReportSha = ReadMeasSha(Receipt.get("native_result_sha256"))
    Approved = KNestProofPins.get(ManifestSha)
    if Approved is None or ReportSha != Approved[0]:
        raise ValueError("nested publication requires authenticated offline evidence")
    return NestMeasure(EpochValue, ManifestSha, ReportSha, Approved[1], Approved[2])
