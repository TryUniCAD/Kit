from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.EmitChmfPart import (
    EmitChmfPart,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.ChmfViewInput import (
    ChmfViewInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    PlanChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import (
    ReadChmfOwn,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from tests.Convert.Solidworks.Research.AdapterBridge.Chamfers.AngleTestModel import (
    MakeAngleDoc,
)


# an independent drawn label must change the angular exterior station without changing either live driver
def TestChmfView() -> None:
    Document = MakeAngleDoc()
    PlanValue = PlanChmfPart(Document)
    Settings = MakePartRecipe(PlanValue.StockValue, 1795510277)
    BasisValue = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
    ViewValue = AnnoViewInput("Stock detail", BasisValue)
    Presentation = ChmfViewInput(
        (ViewValue,),
        ViewValue.NameValue,
        (1.75, -0.00725),
        (-0.005, 0.008),
        0.014,
        True,
        (17, 29),
    )
    for LabelValue, Expected in (
        (Presentation.AngleText, -0.5),
        ((-0.013, -0.0045), 1.5),
    ):
        DisplayValue = ReplaceValue(Presentation, AngleText=LabelValue)
        Candidate = EmitChmfPart(
            Document, ReplaceValue(PlanValue, DisplayValue=DisplayValue), Settings
        )
        Archive = SldprtArchive.from_bytes(Candidate.BytesValue)
        LinkValue = ReadNativeLink(Archive, 0, ReadChamfers=True)
        Owners = ReadChmfOwn(LinkValue, ColdValue=True)
        Distance, Angle = Owners.DriversValue
        assert (Distance.NameValue, Distance.ValueSi) == ("D1", 0.003375)
        assert (Angle.NameValue, Angle.ValueSi) == ("D2", 0.625)
        Fields = Angle.DisplayNode.FieldsValue
        assert Fields["f8a8"] == Expected and Fields["ff80"] == 29
        assert Distance.DisplayNode.FieldsValue["f8b0"] == 0.00725
        assert (
            Distance.DisplayNode.FieldsValue["f2b0"] == Fields["f2b0"] == [{"v": 200}]
        )
