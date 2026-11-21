from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Named.Checks.GetNamedBasis import (
    GetNamedBasis,
)
from convert.adapters.solidworks.Drawing.Definition.Named.Checks.GetNamedScale import (
    GetNamedScale,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewOwners import (
    KViewDirections,
)


# each supported named family must retain its canonical basis selector and independent dimension eligibility
def CheckNamedFrame(ViewValue: ArchiveNode, OrientationValue: str) -> None:
    FieldsValue = ViewValue.FieldsValue
    if (
        OrientationValue not in KViewDirections
        or FieldsValue["f1018"] != OrientationValue
    ):
        raise BodyUnsupported(
            "named drawing Definition has an unsupported or mismatched family"
        )
    FrameValue = NeedConceptMap(FieldsValue["f5e0"])
    Position = NeedConceptMap(FieldsValue["f778"])
    BasisValue = GetNamedBasis(OrientationValue)
    _ = GetNamedScale(ViewValue)
    EligibleValue = sum(abs(BasisValue[Index]) >= 1e-8 for Index in (2, 5, 8)) == 1
    if (
        FieldsValue["f1010"] != KViewDirections[OrientationValue]
        or FrameValue["has_matrix"] != int(OrientationValue != "*Front")
        or FrameValue["f78"] != 0
        or Position["z"] != 0.0
        or int(NeedDrawNumber(FieldsValue["f610"])) & 48
        != (16 if EligibleValue else 32)
    ):
        raise BodyUnsupported(
            "named drawing Definition has an invalid selector frame or eligibility owner"
        )
    if OrientationValue != "*Front":
        MatrixValue = NeedConceptMap(FrameValue["f08"])
        if not all(
            IsClose(
                NeedDrawNumber(MatrixValue[f"m{Index}"]),
                Expected,
                rel_tol=1e-12,
                abs_tol=1e-14,
            )
            for Index, Expected in enumerate(BasisValue)
        ):
            raise BodyUnsupported(
                "named drawing Definition has a noncanonical orientation basis"
            )
    for FieldName in ("f58", "f60", "f68"):
        _ = NeedDrawNumber(FrameValue[FieldName])
    for FieldName in ("x", "y", "z"):
        _ = NeedDrawNumber(Position[FieldName])
