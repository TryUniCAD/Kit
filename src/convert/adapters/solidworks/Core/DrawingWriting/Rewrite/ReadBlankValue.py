from types import UnionType
from typing import cast as CastValue, get_args as TypeArgs, get_origin as TypeOrigin
from uuid import UUID

from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.BlankMetadataTypes import (
    KBlankMetadataTypes,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankOwner import (
    ReadBlankOwner,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankScalar import (
    ReadBlankScalar,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankTuple import (
    ReadBlankTuple,
)


# source intent must use closed official semantic types rather than document supplied class names or binary programs
def ReadBlankValue(TypeValue: object, Value: object) -> object:
    if (
        TypeValue is type(None)
        or TypeValue is str
        or TypeValue is int
        or TypeValue is bool
        or TypeValue is float
        or TypeValue is UUID
    ):
        return ReadBlankScalar(TypeValue, Value)
    Origin = TypeOrigin(TypeValue)
    Arguments = CastValue(tuple[object, ...], TypeArgs(TypeValue))
    if Origin is UnionType:
        Options = tuple(
            Argument
            for Argument in Arguments
            if (Argument is type(None)) == (Value is None)
        )
        if len(Options) != 1:
            raise ValueError("blank metadata union is not a known optional owner")
        return ReadBlankValue(Options[0], Value)
    if Origin is tuple:
        return ReadBlankTuple(Arguments, Value, ReadBlankValue)
    if isinstance(TypeValue, type) and TypeValue in KBlankMetadataTypes:
        return ReadBlankOwner(TypeValue, Value, ReadBlankValue)
    raise ValueError("blank metadata references an unsupported semantic type")
