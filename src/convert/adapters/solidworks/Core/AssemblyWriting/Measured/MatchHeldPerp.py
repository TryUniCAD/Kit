from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# complete member commitments include the embedded native locators without exposing sealed paths
def MatchHeldPerp(
    Receipt: dict[str, object],
    NativePath: str,
    Members: tuple[tuple[str, bytes], ...],
) -> Mapping[str, object]:
    Fingerprints = {
        RoleValue: {"bytes": len(Payload), "sha256": CalcSha(Payload).hexdigest()}
        for RoleValue, (_, Payload) in zip(("child", "parent"), Members, strict=True)
    }
    for SlotValue in ReadMeasRows(Receipt.get("slots"), 2):
        if Fingerprints == ReadMeasMap(SlotValue.get("generated_files")):
            return FreezeMapping(
                {
                    KPartMeasureOpt: FreezeMapping(
                        {
                            "native_result_sha256": ReadMeasSha(
                                SlotValue.get("native_final_sha256")
                            ),
                            "build_lock_sha256": ReadMeasSha(
                                SlotValue.get("build_lock_sha256")
                            ),
                            "preparation_lock_sha256": ReadMeasSha(
                                SlotValue.get("preparation_lock_sha256")
                            ),
                        }
                    ),
                    "required_native_destination": NativePath,
                }
            )
    raise ValueError("perpendicular evidence does not match one exact held-out bundle")
