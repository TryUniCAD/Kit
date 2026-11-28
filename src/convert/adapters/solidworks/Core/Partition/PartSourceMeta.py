from collections.abc import Mapping

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.EquationTarget import KUnresolvedEqTargets
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream
from interchange import frozen_mapping as FrozenMapping


# these source facts describe the archive independently of the selected geometry
def PartSourceMeta(
    Archive: SldprtArchive,
    Model: NativeModel,
    FormatId: str,
    UnresolvedTargets: list[Mapping[str, object]],
) -> Mapping[str, object]:
    return FrozenMapping(
        {
            "adapter": FormatId,
            "file_id": Archive.file_id,
            "native_class_names": tuple(
                dict.fromkeys((ItemValue.name for ItemValue in Model.classes))
            ),
            "native_feature_count": len(Model.features),
            "native_name_record_count": len(Model.names),
            "native_scalar_count": len(Model.scalars),
            "stream_names": tuple((Record.name for Record in Archive.records)),
            **(
                {KUnresolvedEqTargets: tuple(UnresolvedTargets)}
                if UnresolvedTargets
                else {}
            ),
            **(
                {
                    "source_display_units": Model.linear_display.UnitName,
                    "source_display_units_stream": KInformationStream,
                }
                if Model.linear_display is not None
                else {}
            ),
        }
    )
