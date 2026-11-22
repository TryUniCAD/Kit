from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)


# sketch lengths and boss controls must each retain separate live typed owners
def CheckLeafDims(OwnerValue: ExtrudeOwner, DimsValue: LineDims) -> None:
    FieldsValue = OwnerValue.EndValue.FieldsValue
    EndValues = tuple(
        ReadPrismParam(FieldsValue.get(FieldName), Angular)
        for FieldName, Angular in (
            ("f18", False),
            ("f20", False),
            ("fc8", True),
            ("fd0", True),
        )
    )
    Primary, Secondary, ForwardDraft, BackwardDraft = EndValues
    DepthValue = OwnerValue.DepthValue
    if (
        Primary[:2] != (DepthValue.Dimension, DepthValue.Parameter)
        or Secondary[2] != Primary[2]
        or ForwardDraft[2] != 0
        or BackwardDraft[2] != 0
    ):
        raise ValueError("dimensioned cold leaf has independent inactive end controls")
    Drivers = (
        *EndValues,
        *(
            (Driver.NodeValue, Driver.ParamValue, Driver.MetresValue)
            for Driver in DimsValue.DriverValues
        ),
    )
    if len({Dimension.FieldsValue["f50"] for Dimension, _, _ in Drivers}) != len(
        Drivers
    ) or len({Parameter for _, Parameter, _ in Drivers}) != len(Drivers):
        raise ValueError("dimensioned cold leaf requires distinct driving owners")
