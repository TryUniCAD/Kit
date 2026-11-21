from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import (
    MakeAsmCase,
)


# ordered neutral plans vary mate publication order independently of geometry while retaining disjoint generated bodies and analytically compatible principal plane relations
def MakeOrderCase(KindOrder: tuple[str, ...], IsVariant: bool) -> dict[str, object]:
    Request = MakeAsmCase("distance", "x", IsVariant)
    AssemblyValue = CastValue(dict[str, object], Request["assembly"])
    NameValue = (
        "SdkOrdered"
        + "".join(Value[0].upper() for Value in KindOrder)
        + ("Beta" if IsVariant else "Alpha")
    )
    AssemblyValue["name"] = NameValue
    OutputValue = CastValue(dict[str, object], AssemblyValue["output"])
    OutputValue["path_name"] = "C:\\KitSdkCandidates\\" + NameValue + ".SLDASM"
    Occurrences = CastValue(list[dict[str, object]], Request["occurrences"])
    First = Occurrences[0]
    OriginValue = CastValue(tuple[float, float, float], First["origin"])
    AxisFirst = CastValue(tuple[float, float, float], First["u"])
    Occurrences[1]["origin"] = tuple(
        Value + 0.04353 * Normal + float(IndexValue == 2) * 0.1074
        for IndexValue, (Value, Normal) in enumerate(
            zip(OriginValue, AxisFirst, strict=True)
        )
    )
    AxesValue = {"coincident": "y", "parallel": "z", "distance": "x"}
    Request["mates"] = [
        {
            "kind": KindValue,
            "name": "Authored" + KindValue.title(),
            "axis": AxesValue[KindValue],
            "fixed_occurrence": int(IsVariant),
            "distance_m": 0.04353,
            "design_intent": False,
            "selected_leader": 0,
        }
        for KindValue in KindOrder
    ]
    del Request["mate"]
    return Request
