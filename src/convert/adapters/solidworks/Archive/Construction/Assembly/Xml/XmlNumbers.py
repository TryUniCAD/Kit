from collections.abc import Iterable


# native ordinary assembly xml renders every placement and bounding coordinate with the independently verified sixteen significant digit rule
def XmlNumbers(Values: Iterable[float | int]) -> str:
    return " ".join(format(ItemValue, ".16g") for ItemValue in Values)
