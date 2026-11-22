from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# a flipped offset translates along the base normal while keeping the original ordered basis
def OffsetFrame(BaseValue: PlaneFrame, DistanceValue: float) -> PlaneFrame:
    XValue, YValue, ZValue = BaseValue.OriginValue
    NormalX, NormalY, NormalZ = BaseValue.NormalValue
    return PlaneFrame(
        (
            XValue + DistanceValue * NormalX,
            YValue + DistanceValue * NormalY,
            ZValue + DistanceValue * NormalZ,
        ),
        BaseValue.AxisU,
        BaseValue.AxisV,
        BaseValue.NormalValue,
    )
