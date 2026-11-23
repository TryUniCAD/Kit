from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# the neutral bundle must reproduce the same root and linked member bytes at the measured namespace
def MatchPlanarMeas(
    Receipt: dict[str, object],
    NativePath: str,
    Members: tuple[tuple[str, bytes], ...],
) -> Mapping[str, object]:
    Parent = PureWindowsPath(NativePath)
    if (
        len(Members) != 2
        or Receipt.get("root") != Parent.name
        or Receipt.get("namespace") != str(Parent.parent)
        or str(Parent) != NativePath
    ):
        raise ValueError("planar assembly measurement has a different native locator")
    RowsValue = ReadMeasRows(Receipt.get("members"), 2)
    for (NameValue, Payload), RowValue in zip(Members, RowsValue, strict=True):
        if RowValue != {
            "name": NameValue,
            "bytes": len(Payload),
            "sha256": CalcSha(Payload).hexdigest(),
        }:
            raise ValueError(
                f"planar assembly measurement does not match the exact member {NameValue}"
            )
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "native_result_sha256": ReadMeasSha(
                        Receipt.get("native_result_sha256")
                    ),
                    "packet_sha256": ReadMeasSha(Receipt.get("packet_sha256")),
                    "fixture_sha256": ReadMeasSha(Receipt.get("fixture_sha256")),
                }
            ),
            "required_native_destination": NativePath,
        }
    )
