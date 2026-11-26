from convert.adapters.solidworks.Archive.Construction.Model.EmptyBodyProps import (
    EmptyBodyProps,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartZeroes import (
    KPartZeroes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# concrete part state must extend common model fields without assigning assembly meanings to overlapping offsets
def MakePartSeeds(HatchName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {FieldName: 0 for FieldName in KPartZeroes}
    FieldsValue.update(
        {FieldName: () for FieldName in ("f1108", "f1130", "f1628", "f16e8", "f1640")}
    )
    FieldsValue.update({FieldName: 0 for FieldName in ("n1118", "n1140", "n16f8")})
    FieldsValue.update(
        {
            "f938": EmptyBodyProps(True),
            "f1c70": EmptyRootRows(),
            "f1420": None,
            "f13f8": None,
            "f1418": ArchiveNode(
                RuntimeClass("gcXhatch_c", 1),
                {
                    "f08": HatchName,
                    "f10": 0.0,
                    "f18": 1.0,
                    "f34": 0,
                    "f20": 0,
                    "f24": 1,
                    "f28": -1,
                    "f2c": -1,
                    "f30": 0,
                },
            ),
            "f1588": ArchiveNode(
                RuntimeClass("uoModelData_c", 1), {"f08": None, "f10": 0}
            ),
            "f1104": 20,
            "f1128": 20,
            "f18d8": 101,
        }
    )
    return FieldsValue
