from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeDrawFeature import (
    MakeDrawFeature,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ProfileTime import (
    MakeProfileTime,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ScaleFrame import (
    MakeScaleFrame,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# empty drawing profiles must apply the sheet reset after the shared local sketch constructor
def MakeSheetSketch(
    SheetValue: ArchiveNode, PlaneReference: ArchiveNode, BuildValue: SheetBuild
) -> ArchiveNode:
    ProfileValue = MakeDrawFeature(
        "moProfileFeature_c",
        BuildValue.NamesValue.ProfileName,
        SheetValue,
        BuildValue.FirstIdValue + 2,
        BuildValue,
    )
    SketchValue = MakeSketchSeed(ProfileValue)
    SketchValue.FieldsValue["f128"] = 0
    Dimensions = NeedConceptMap(SketchValue.FieldsValue["dims"])
    for ListValue in (
        NeedConceptNode(SketchValue.FieldsValue["f5d8"], "suObList"),
        NeedConceptNode(Dimensions["f118"], "suObList"),
    ):
        if ListValue.FieldsValue["items"]:
            raise ValueError(
                "drawing sheet seed unexpectedly contains owned sketch entities"
            )
        ListValue.FieldsValue["items"] = ()
    ProfileValue.FieldsValue.update(MakeProfileTime(BuildValue.CreatedAtValue))
    ProfileValue.FieldsValue.update(
        {
            "f35c": 0,
            "f390": 0,
            "orig_dim_feature": None,
            "f3dc": 0,
            "pd_f80": SketchValue,
            "d5c0": {"n2a8": 0, "f2a8": (), "f2b0": 0},
            "ca30": {
                "n238": 0,
                "f238": (),
                "f10": 3,
                "f198": {"empty": 1},
                "f168": {"n": 0, "items": ()},
                "f188": {"elem": 0},
            },
            "f3e0": 100000,
            "f3e8": {"n": 0, "items": ()},
            "f3b8": None,
            "write_ref": 1,
            "pd_f78": PlaneReference,
            "pd_ff0": MakeScaleFrame(
                1.0
                / (
                    BuildValue.InputValue.NumeratorValue
                    / BuildValue.InputValue.DenominatorValue
                )
            ),
            "pd_has_fe8": 0,
            "pd_f100": 4,
            "pd_f110": None,
            "pd_f11c": -1,
            "pd_f118": 0,
            "pd_f2a0": 101,
            "f3c0": 0,
            "f388": None,
            "pd_f128": {"n": 0, "items": ()},
            "pd_f148": {"n": 0, "items": ()},
            "f42c": 0,
        }
    )
    return ProfileValue
