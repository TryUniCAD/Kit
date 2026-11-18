from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# an ordinary regenerated model view owns empty display caches while its style and model flags come from the actual generated documents
def MakeViewState(
    ModelValue: ArchiveNode, ChildValue: PartCandidate, NormalValue: tuple[float, ...]
) -> dict[str, object]:
    DetailValue = NeedConceptMap(ModelValue.FieldsValue["fae0"])
    StateValue: dict[str, object] = dict.fromkeys(
        (
            "f798",
            "f79c",
            "has_f6c8",
            "has_f8e0",
            "f7bc",
            "f7a8",
            "f7c0",
            "f7b4",
            "f8ec",
            "has_f9d8",
            "na10",
            "has_fb50",
            "n860",
            "na18",
            "fb74",
            "f8e8",
            "fd94",
            "fdb8",
            "has_fe78",
            "fe8c",
            "nf50",
            "nf68",
            "f540",
            "ffa4",
            "ffb4",
            "f558",
            "has_view_bodies",
            "ffbc",
            "f590",
            "f1010",
            "f1020",
            "f1028",
            "f102c",
        ),
        0,
    )
    StateValue.update(dict.fromkeys(("f9e8", "f9f0", "f9f8", "fa00", "fb68"), 0.0))
    StateValue.update(
        dict.fromkeys(("f968", "f8f8", "f640", "f658", "fb58", "f1008"), None)
    )
    StateValue.update(dict.fromkeys(("fe30_name", "f548", "f550", "fff8"), ""))
    StateValue.update(dict.fromkeys(("f858", "ff48", "ff60"), ()))
    StateValue.update(
        {
            NameValue: EmptyRootRows()
            for NameValue in (
                "fd28",
                "f900",
                "fb78",
                "fa20",
                "fa68",
                "fab0",
                "faf8",
                "fc28",
                "fc70",
                "fcb8",
                "fd48",
                "ff70",
            )
        }
    )
    StateValue.update(
        {
            "f6b8": IdentityXform(),
            "f6c0": IdentityXform(),
            "f608": {
                f"b{Index}": Value
                for Index, Value in enumerate(
                    (0.0, 0.0, 0.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, -2.0)
                )
            },
            "fe30_flags": -1,
            "f7ac": 2,
            "f7b0": 2,
            "f8f0": -1,
            "f6b0": -1.0,
            "fe40": 3,
            "f410": -1,
            "f3e8": 0.01,
            "f3f0": 0.003175,
            "fe94": FieldInt(ChildValue.SystemValue.RootValue.FieldsValue, "ff3c"),
            "ffa8": FieldInt(DetailValue, "f15c"),
            "ffac": FieldInt(DetailValue, "f160"),
            "f7a0": FieldInt(DetailValue, "f2c6c"),
            "f55c": -1,
            "f594": -1,
            "f3f8": 1.0,
            "f5a8": 1,
            "f1030": 1,
            "f610": (1 << 11)
            | (1 << 7)
            | (1 << (4 if sum(abs(Value) >= 1e-8 for Value in NormalValue) == 1 else 5))
            | (1 << 3),
            "f614": sum(1 << Index for Index in (2, 8, 10, 16, 20, 21, 22)),
            "f618": ((1 << 15) if FieldInt(DetailValue, "f20") & (1 << 18) else 0),
            "f61c": (1 << 3) | (1 << 2) | 1,
        }
    )
    return StateValue
