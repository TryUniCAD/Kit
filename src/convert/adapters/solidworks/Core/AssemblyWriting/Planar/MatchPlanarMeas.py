from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from interchange.Core.Common import FreezeMapping


# planar and rigid nested publications need distinguishable measured bundle contracts
KPlanarMeasSchema = "kit.sw2026.planar-assembly-measurement.v1"


# native evidence binds the ordered companion and assembly at their exact output locator
def MatchPlanarMeas(
    Receipt: dict[str, object],
    NativePath: PureWindowsPath,
    MemberValues: tuple[tuple[str, bytes], ...],
) -> Mapping[str, object]:
    RowsValue = ReadMeasRows(Receipt.get("members"), len(MemberValues))
    if (
        len(RowsValue) != len(MemberValues)
        or Receipt.get("root") != NativePath.name
        or Receipt.get("namespace") != str(NativePath.parent)
    ):
        raise ValueError("planar assembly measurement has a different native locator")
    for (NameValue, RawValue), RowValue in zip(MemberValues, RowsValue, strict=True):
        if type(RowValue.get("bytes")) is not int or RowValue != {
            "name": NameValue,
            "bytes": len(RawValue),
            "sha256": CalcSha(RawValue).hexdigest(),
        }:
            raise ValueError(
                f"planar assembly measurement does not match the exact member {NameValue}"
            )
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    NameValue: Receipt[NameValue]
                    for NameValue in (
                        "native_result_sha256",
                        "packet_sha256",
                        "fixture_sha256",
                    )
                }
            )
        }
    )
