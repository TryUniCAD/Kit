from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
    KAnnoBasis,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    ReadAnnoBasis,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.ChmfViewInput import (
    ChmfViewInput,
)


# actual model views may reverse both display axes while the selected carriers keep their directions
def PickChmfView(
    IntentValue: ChmfViewInput, StockBasis: KAnnoBasis
) -> tuple[AnnoViewInput, float]:
    HitsValue = tuple(
        ModelView
        for ModelView in IntentValue.CatalogValue
        if ModelView.NameValue == IntentValue.DriverView
    )
    if len(HitsValue) != 1:
        raise ValueError("chamfer requires one actual named driver view in its catalog")
    (ViewValue,) = HitsValue
    BasisValue = ReadAnnoBasis(ViewValue.BasisValue)
    AxisU, AxisV, Normal = StockBasis
    ReversedBasis = (
        (-AxisU[0], -AxisU[1], -AxisU[2]),
        (-AxisV[0], -AxisV[1], -AxisV[2]),
        Normal,
    )
    if BasisValue not in (StockBasis, ReversedBasis):
        raise ValueError("chamfer driver view does not own both signed incident axes")
    SenseValue = 1.0 if BasisValue == StockBasis else -1.0
    if IntentValue.DistanceText[1] * SenseValue <= 0.0:
        raise ValueError("chamfer distance clearance has the wrong signed witness side")
    return ViewValue, SenseValue
