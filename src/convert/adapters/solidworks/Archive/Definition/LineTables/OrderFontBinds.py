from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import (
    FontBinding,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.FontKeyHash import (
    FontKeyHash,
)


# the selected map constructor has seventeen buckets and new keys prepend before upward bucket traversal
def OrderFontBinds(
    BindingValues: tuple[FontBinding, ...],
) -> tuple[FontBinding, ...]:
    BucketValues: list[list[FontBinding]] = [[] for _ in range(17)]
    for BindingValue in BindingValues:
        if type(BindingValue) is not FontBinding:
            raise TypeError("line font order requires typed category bindings")
        BucketValues[FontKeyHash(BindingValue.CategoryValue) % 17].insert(
            0, BindingValue
        )
    return tuple(Value for BucketValue in BucketValues for Value in BucketValue)
