from interchange.geometry.Models.BoundingBox import BoundingBox


# exact orthogonal boxes require positive separation before a selected cut is composed
def CheckStockGap(FirstValue: BoundingBox, SecondValue: BoundingBox) -> None:
    FirstMin, FirstMax = FirstValue.minimum, FirstValue.maximum
    SecondMin, SecondMax = SecondValue.minimum, SecondValue.maximum
    if not (
        FirstMax.x < SecondMin.x
        or SecondMax.x < FirstMin.x
        or FirstMax.y < SecondMin.y
        or SecondMax.y < FirstMin.y
        or FirstMax.z < SecondMin.z
        or SecondMax.z < FirstMin.z
    ):
        raise ValueError("the two original stocks must have positive separation")
