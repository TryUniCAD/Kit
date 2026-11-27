from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure


# scan only authorized completed lifecycles and bind the result to the full archive
def MatchImportMeas(
    Payload: bytes, Measurements: tuple[ImportMeasure, ...]
) -> ImportMeasure:
    SizeValue = len(Payload)
    CandidateSha = CalcSha(Payload).hexdigest()
    for MeasureValue in Measurements:
        if (
            MeasureValue.SizeValue == SizeValue
            and MeasureValue.CandidateSha == CandidateSha
        ):
            return MeasureValue
    raise ValueError("regenerated local solid has no exact native measurement")
