from dataclasses import replace as ReplaceValue
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.AttachCircError import (
    AttachCircError,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.IsRadiusSketch import (
    IsRadiusSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.BindSavedCircle import (
    BindSavedCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved family with extra native owners keeps its earlier compatibility projection
def TrySavedCircle(
    Model: NativeModel, Archive: SldprtArchive, *, Strict: bool
) -> NativeModel:
    Markers = Model.sketches[0].markers
    if (
        Model.equations
        or len(Model.configurations) != 1
        or not any(Marker.semantic == "circle" for Marker in Markers)
        or not any(
            Marker.endpoint_indices is not None
            and Marker.endpoint_indices[0] == Marker.endpoint_indices[1]
            for Marker in Markers
        )
    ):
        return Model
    try:
        LinkValue = ReadNativeLink(Archive, Model.active_configuration_id)
        Features = IndexFeatures(LinkValue)
        Profile = RequireNative(
            Features[Model.sketches[0].object_id], "moProfileFeature_c"
        )
        ShapeValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
        if not ShapeValue.FieldsValue.get("arcs"):
            return Model
    except (KeyError, TypeError, ValueError, OverflowError):
        return Model
    Attached = IsRadiusSketch(ShapeValue)
    try:
        return BindSavedCircle(Model, LinkValue, Features, Profile, Archive)
    except (KeyError, TypeError, ValueError, OverflowError) as ErrorInfo:
        if Strict and (Attached or isinstance(ErrorInfo, AttachCircError)):
            raise SldprtFormatError(str(ErrorInfo)) from ErrorInfo
        return ReplaceValue(
            Model,
            diagnostics=(
                *Model.diagnostics,
                f"saved circle typed owners unavailable: {ErrorInfo}",
            ),
        )
