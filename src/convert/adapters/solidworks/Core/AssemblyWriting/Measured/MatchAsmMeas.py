from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from interchange.Core.Common import FreezeMapping


# every real member must match the measured namespace and ordered dependency closure
def MatchAsmMeas(
    Receipt: dict[str, object],
    PlanValue: NestedAsmPlan,
    Candidates: tuple[tuple[PureWindowsPath, TargetDocument], ...],
) -> Mapping[str, object]:
    MemberRows = ReadMeasRows(Receipt.get("members"))
    if (
        len(MemberRows) != len(Candidates)
        or type(Receipt.get("root")) is not str
        or Receipt["root"] != PlanValue.RootValue.id
        or type(Receipt.get("namespace")) is not str
        or Receipt["namespace"] != str(Candidates[-1][0].parent)
    ):
        raise ValueError(
            "native assembly measurement has a different root namespace or member closure"
        )
    for Definition, (PathValue, Target), RowValue in zip(
        PlanValue.OrderedDefinitions, Candidates, MemberRows, strict=True
    ):
        Children = [
            Value for Value, _ in PlanValue.PlacementsValue.get(Definition.id, ())
        ]
        if type(RowValue.get("bytes")) is not int or RowValue != {
            "id": Definition.id,
            "name": PathValue.name,
            "configuration": Definition.configuration_name,
            "children": Children,
            "bytes": len(Target.BytesValue),
            "sha256": CalcSha(Target.BytesValue).hexdigest(),
        }:
            raise ValueError(
                f"native assembly measurement does not match the exact member {PathValue.name}"
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
            ),
        }
    )
