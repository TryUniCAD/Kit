from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart

# the registered perpendicular report binds both sealed native pairs
KHeldPerpSchema = "kit.sw2026.public-perpendicular-heldout-registration.v1"

# the canonical report authenticates both complete member digest pairs
KHeldPerpSha = "f5a5f7640e1719898eda1d691fb20c3afad63a8c57a284c3b6a53b81f8274f68"


# snapshot the sealed lifecycle record before any archive construction can run
def ReadHeldPerp(ReceiptValue: dict[str, object]) -> dict[str, object]:
    Encoded = DumpJson(
        ReceiptValue,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        ensure_ascii=False,
    ).encode("utf-8")
    if CalcSha(Encoded).hexdigest() != KHeldPerpSha:
        raise ValueError("perpendicular publication requires authenticated held-out evidence")
    Receipt = ReadMeasMap(LoadJson(Encoded))
    Slots = ReadMeasRows(Receipt.get("slots"), 2)
    if (
        Receipt.get("schema") != KHeldPerpSchema
        or Receipt.get("oracle_file_version") != KOraclePart["build"]
        or Receipt.get("oracle_sha256") != KOraclePart["sha256"]
        or Receipt.get("passed") is not True
        or Receipt.get("same_original_prewriter_source_locks_used_for_public_route")
        is not True
        or Receipt.get("native_numeric_checks") != 484
        or Receipt.get("distinct_native_processes") != 12
        or Receipt.get("healthy_control_processes") != 4
        or Receipt.get("strict_source_and_saved_readbacks_passed") != 6
        or len(Slots) != 2
    ):
        raise ValueError("perpendicular evidence requires both held-out native lifecycles")
    return Receipt
