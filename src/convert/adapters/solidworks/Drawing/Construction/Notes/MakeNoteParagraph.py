from collections.abc import Mapping

from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# generic text and each line retain independent paragraph owners with actual document spacing
def MakeNoteParagraph(
    StyleValue: Mapping[str, object], LineValue: bool
) -> dict[str, object]:
    Spacing = NeedDrawNumber(StyleValue["f78"])
    ParagraphSpacing = (
        Spacing if Spacing < 1.0 and (not LineValue or Spacing > 0.0) else 0.001
    )
    return {
        "f00": 0,
        "f08": 0.0,
        "f10": 0.0,
        "f18": 0.01,
        "f20": 0,
        "f24": 0,
        "f28": "$$.",
        "f30": 0,
        "f34": 0,
        "f38": 0,
        "f40": 0.0,
        "f48": 0.0,
        "f50": 0,
        "f58": ParagraphSpacing,
        "f60": 0.001,
        "f68": 0,
        "f6c": -1,
    }
