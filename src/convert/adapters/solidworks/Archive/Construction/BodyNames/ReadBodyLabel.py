from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid


# an authored body label must retain its real neutral owner before ordinary geometry admission can be reused
def ReadBodyLabel(DocumentValue: CadDocument) -> str:
    if type(DocumentValue) is not CadDocument:
        raise TypeError("named part requires an actual neutral document")
    AssertValid(DocumentValue)
    if (len(DocumentValue.bodies), len(DocumentValue.feature_timeline)) != (1, 1):
        raise ValueError("named part requires one body and one creating feature")
    BodyValue = DocumentValue.bodies[0]
    if BodyValue.final_feature_id != DocumentValue.feature_timeline[0].id:
        raise ValueError("named body must belong to its actual creating feature")
    NameValue = BodyValue.name
    if NameValue == DocumentValue.feature_timeline[0].name:
        return NameValue
    if type(NameValue) is not str or not NameValue or NameValue != NameValue.strip():
        raise ValueError("named body requires explicit nonempty untrimmed text")
    try:
        UnitCount = len(NameValue.encode("utf-16-le")) // 2
    except UnicodeEncodeError:
        raise ValueError(
            "named body requires valid paired unicode code units"
        ) from None
    if not NameValue.isprintable() or not 1 <= UnitCount <= 255:
        raise ValueError(
            "named body requires printable text within the cold label bound"
        )
    return NameValue
