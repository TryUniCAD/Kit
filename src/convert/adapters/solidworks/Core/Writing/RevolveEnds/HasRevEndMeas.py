from typing import cast as CastValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)


# the end batch has its own evidence authority and must retain separate dispatch from principal revolve receipts
def HasRevEndMeas(OptionsValue: WriteOptions | None) -> bool:
    if not isinstance(OptionsValue, WriteOptions):
        return False
    Envelope = OptionsValue.values.get(KPartMeasureOpt)
    if type(Envelope) is not dict:
        return False
    Receipt = CastValue(dict[str, object], Envelope).get("receipt")
    return type(Receipt) is dict and "generation_receipt" in CastValue(
        dict[str, object], Receipt
    )
