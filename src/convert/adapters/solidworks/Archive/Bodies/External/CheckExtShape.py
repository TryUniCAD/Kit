from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.External.CheckExtFields import (
    CheckExtFields,
)


# manager external features retain their measured null reference ownership boundary
def CheckExtShape(FieldsValue: Mapping[str, object]) -> None:
    CheckExtFields(FieldsValue)
    if FieldsValue["f50"] is not None:
        raise BodyUnsupported("unsupported native external feature reference profile")
