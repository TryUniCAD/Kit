from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Distance.DistanceCut import DistanceCut


# independent input operands must define expected attribution without reusing matcher implementation or trusting report fields
def MakeRefDeltas(
    First: CadDocument, Second: CadDocument, Family: str, RoleName: str
) -> list[dict[str, object]]:
    Before, After = First.feature_timeline[-1], Second.feature_timeline[-1]
    LeftIds, RightIds = Before.OutputBodyIds, After.OutputBodyIds
    if Family == "cut_targets":
        assert isinstance(Before.definition, DistanceCut)
        assert isinstance(After.definition, DistanceCut)
        LeftIds, RightIds = (
            Before.definition.TargetBodyIds,
            After.definition.TargetBodyIds,
        )
    Expected: list[dict[str, object]] = []
    for Index, (LeftBody, RightBody) in enumerate(zip(LeftIds, RightIds)):
        for BodyId, LeftCount, RightCount in (
            (LeftBody, 1, 0),
            (RightBody, 0, 1),
        ):
            Expected.append(
                {
                    "left": Before.id,
                    "right": After.id,
                    "role": RoleName + "/" + str(Index),
                    "left_target": BodyId,
                    "right_target": BodyId,
                    "left_count": LeftCount,
                    "right_count": RightCount,
                    "reason": "target_multiplicity",
                }
            )
    return Expected
