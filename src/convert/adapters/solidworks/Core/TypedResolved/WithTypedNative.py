from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.TryWidthDepth import (
    TryWidthDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.ProjectTyped import ProjectTyped
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# unsupported typed modes must stay explicit while established public readers retain their prior behavior
def WithTypedNative(Model: NativeModel, Archive: SldprtArchive) -> NativeModel:
    try:
        return ProjectTyped(
            Model, ReadNativeLink(Archive, Model.active_configuration_id)
        )
    except (ValueError, TypeError, KeyError) as ErrorInfo:
        Related = TryWidthDepth(Model, Archive)
        if Related is not None:
            return Related
        return ReplaceValue(
            Model,
            diagnostics=(
                *Model.diagnostics,
                f"typed resolved semantics unavailable: {ErrorInfo}",
            ),
            TypedGraph={
                "status": "unsupported",
                "archive_version": ContainerMo(Archive.streams),
                "configuration_id": Model.active_configuration_id,
                "diagnostic": str(ErrorInfo),
                "full_linked_graph": False,
                "typed_geometry_projection": False,
                "typed_assembly_mates": False,
                "public_writer_qualified": False,
            },
        )
