# the qualified grammar change must leave every other byte of the geometry evidence pinned
def NormalizeSigned(ReportBytes: bytes) -> bytes:
    HistoricRefusal = b'"unwrapped_literal": "Native reverse distance requires a wrapped millimeter literal"'
    CurrentRefusals = (
        b'"reverse_formula": "Native reverse distance requires a wrapped millimeter literal"',
        b'"reverse_formula": "Native reverse distance requires a negative millimeter literal"',
    )
    MatchedRefusals = tuple(
        CurrentRefusal
        for CurrentRefusal in CurrentRefusals
        if ReportBytes.count(CurrentRefusal) == 1
    )
    assert len(MatchedRefusals) == 1, "Expected exactly one qualified formula refusal"
    assert ReportBytes.count(HistoricRefusal) == 0
    return ReportBytes.replace(MatchedRefusals[0], HistoricRefusal, 1)
