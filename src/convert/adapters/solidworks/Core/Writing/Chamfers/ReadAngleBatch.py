from convert.adapters.solidworks.Core.Writing.Chamfers.ReadPairReport import (
    ReadPairReport,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart

# the disclosed trial pins the actual generated locators and full artifact digests
KAngleTrialSha = "8db08a479cd2b3e29dd4d5ad38eec3e96631e0aec15f71868a37aea51d423f49"

# the signed side native terminal binds both lifecycles and both healthy controls
KAngleNativeSha = "d161909999b3ed8d72f0885dbb6dbc0dfa3866e712dc4dd390aef7406c236409"


# exact offline documents must identify one complete controlled native batch
def ReadAngleBatch(
    Receipt: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    if set(Receipt) != {"trial", "native_result"}:
        raise ValueError(
            "angle-distance chamfer requires its exact offline measurement"
        )
    Trial, TrialHash = ReadPairReport(Receipt["trial"])
    Native, NativeHash = ReadPairReport(Receipt["native_result"])
    if TrialHash != KAngleTrialSha or NativeHash != KAngleNativeSha:
        raise ValueError(
            "angle-distance chamfer requires authenticated offline evidence"
        )
    if (
        Native.get("manifest_sha256") != TrialHash
        or Trial.get("oracle_build") != KOraclePart["build"]
        or Trial.get("oracle_sha256") != KOraclePart["sha256"]
        or Native.get("proper_distinct_lifetimes") is not True
        or Native.get("healthy_controls") is not True
        or Native.get("passed") is not True
    ):
        raise ValueError("angle-distance chamfer lacks a passing controlled lifecycle")
    return Trial, Native
