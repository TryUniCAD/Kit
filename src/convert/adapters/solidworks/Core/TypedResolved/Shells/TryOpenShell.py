from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Shells.BindShellModel import (
    BindShellModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.ReadOpenShell import (
    ReadOpenShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.ShellPartRead import (
    ShellPartRead,
)

# unresolved shells need a specific strict refusal and permissive diagnostic
KShellRejected = "SOLIDWORKS 2026 shell history requires the linked single inward top cap and a qualified body"


# known source types must still identify shell history without a decoded operation
def IsShellFeature(FeatureValue: NativeFeature) -> bool:
    return (
        FeatureValue.class_name == "moShell_c"
        or FeatureValue.kind.casefold().strip() == "shell"
    )


# strict reads never expose guessed face matches for a known current shell
def TryOpenShell(
    Archive: SldprtArchive, ModelValue: NativeModel, Settings: ReadOptions
) -> tuple[NativeModel, ShellPartRead | None]:
    if (
        Settings.extract_raw_brep
        or Archive.format_version != 4
        or not (
            any(Value.name == "moShell_c" for Value in ModelValue.classes)
            or any(IsShellFeature(Value) for Value in ModelValue.features)
        )
        or ContainerMo(Archive.streams) != 19000
    ):
        return ModelValue, None
    try:
        if (
            ModelValue.active_configuration_id != 0
            or tuple(
                (Value.configuration_id, Value.name)
                for Value in ModelValue.configurations
            )
            != ((0, "Default"),)
            or tuple(Value.kind for Value in ModelValue.operations) != ("join", "shell")
        ):
            raise ValueError(
                "SOLIDWORKS shell does not have the witnessed default model and stock"
            )
        ReadValue = ReadOpenShell(Archive, ModelValue)
        return BindShellModel(ModelValue, ReadValue), ReadValue
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as ErrorInfo:
        if Settings.strict:
            raise SldprtFormat(KShellRejected) from ErrorInfo
        Operations = tuple(
            (
                ReplaceValue(
                    Value,
                    selection_offsets=(),
                    selected_local_ids=(),
                    selection_references=(),
                )
                if Value.kind == "shell"
                else Value
            )
            for Value in ModelValue.operations
        )
        return (
            ReplaceValue(
                ModelValue,
                operations=Operations,
                diagnostics=(*ModelValue.diagnostics, KShellRejected),
            ),
            None,
        )
