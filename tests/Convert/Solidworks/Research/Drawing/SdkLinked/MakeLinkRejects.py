from copy import deepcopy as CopyValue
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


# actual portable drawing mutations must reject unresolved ownership unsupported view families and contradictory derived geometry at the complete file boundary
def MakeLinkRejects(JobValue: dict[str, object]) -> dict[str, dict[str, object]]:
    DataValue = FromData(JobValue["drawing_document"])
    if type(DataValue) is not DrawingData:
        raise TypeError("linked rejection input must retain a real drawing document")
    SheetValue, Reference = DataValue.Sheets[0], DataValue.ModelRefs[0]
    ViewValue = SheetValue.Views[0]
    ViewChanges = (
        ("view_ref", ReplaceValue(ViewValue, ModelRefId="missing model")),
        (
            "configuration",
            ReplaceValue(ViewValue, ConfigurationName="missing configuration"),
        ),
        ("orientation", ReplaceValue(ViewValue, OrientationName="*Back")),
        ("no_orientation", ReplaceValue(ViewValue, OrientationName=None)),
        ("inherited_scale", ReplaceValue(ViewValue, ScaleRatio=None)),
        ("zero_scale", ReplaceValue(ViewValue, ScaleRatio=(0.0, 1.0))),
        ("boolean_scale", ReplaceValue(ViewValue, ScaleRatio=(True, 1.0))),
        ("denominator", ReplaceValue(ViewValue, ScaleRatio=(1.0, 2.0))),
        ("zero_denominator", ReplaceValue(ViewValue, ScaleRatio=(1.0, 0.0))),
        (
            "boolean_position",
            ReplaceValue(ViewValue, PositionValue=PlaneVector(True, 0.1)),
        ),
        ("view_name", ReplaceValue(ViewValue, EntityName="invalid@view")),
        ("duplicate_id", ReplaceValue(ViewValue, EntityId=SheetValue.EntityId)),
        ("outline_cache", ReplaceValue(ViewValue, OutlineValues=(0.0, 0.0, 1.0, 1.0))),
        ("transform_cache", ReplaceValue(ViewValue, ModelToSheet=TransformMatrix())),
    )
    DrawingChanges = (
        ("active_sheet", ReplaceValue(DataValue, ActiveSheetId="missing sheet")),
        ("no_models", ReplaceValue(DataValue, ModelRefs=())),
        ("two_models", ReplaceValue(DataValue, ModelRefs=DataValue.ModelRefs * 2)),
        ("two_sheets", ReplaceValue(DataValue, Sheets=DataValue.Sheets * 2)),
        (
            "no_views",
            ReplaceValue(DataValue, Sheets=(ReplaceValue(SheetValue, Views=()),)),
        ),
        (
            "two_views",
            ReplaceValue(
                DataValue,
                Sheets=(ReplaceValue(SheetValue, Views=SheetValue.Views * 2),),
            ),
        ),
        (
            "model_path",
            ReplaceValue(
                DataValue,
                ModelRefs=(
                    ReplaceValue(Reference, SourcePath="C:\\missing\\different.SLDPRT"),
                ),
            ),
        ),
        (
            "model_format",
            ReplaceValue(
                DataValue, ModelRefs=(ReplaceValue(Reference, SourceFormatId="step"),)
            ),
        ),
    )
    ResultsValue: dict[str, dict[str, object]] = {}
    for Label, DrawingValue in (
        *DrawingChanges,
        *(
            (
                Label,
                ReplaceValue(
                    DataValue, Sheets=(ReplaceValue(SheetValue, Views=(ViewValue,)),)
                ),
            )
            for Label, ViewValue in ViewChanges
        ),
    ):
        FreshJob = CopyValue(JobValue)
        FreshJob["drawing_document"] = CastValue(object, ToData(DrawingValue))
        ResultsValue[Label] = FreshJob
    FreshJob = CopyValue(JobValue)
    CastValue(dict[str, object], FreshJob["support_names"])["sheet_plane"] = ""
    ResultsValue["support_name"] = FreshJob
    FreshJob = CopyValue(JobValue)
    CastValue(dict[str, object], FreshJob["native"])[
        "unknown_annotation"
    ] = "unrepresented"
    ResultsValue["unknown_native"] = FreshJob
    FreshJob = CopyValue(JobValue)
    PartValue = CastValue(dict[str, object], FreshJob["part"])
    CastValue(dict[str, object], PartValue["settings"])[
        "unknown_material"
    ] = "unrepresented"
    ResultsValue["unknown_part"] = FreshJob
    return ResultsValue
