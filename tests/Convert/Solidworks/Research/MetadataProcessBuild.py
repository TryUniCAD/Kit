from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType
from typing import cast as CastValue


# process coverage needs the actual metadata constructor isolated from decoding and reporting responsibilities
def BuildStreams(
    InputData: dict[str, dict[str, object]],
    MetadataModule: ModuleType,
    RegistryValue: object,
) -> dict[str, bytes]:
    return CastValue(
        dict[str, bytes],
        GetAttr(MetadataModule, "streams")(
            registry=RegistryValue,
            header2=GetAttr(MetadataModule, "header")(**InputData["header2"]),
            model_headers={
                int(Index): GetAttr(MetadataModule, "header")(
                    **CastValue(dict[str, object], Values)
                )
                for Index, Values in InputData["model_headers"].items()
            },
            biography_record=GetAttr(MetadataModule, "biography")(),
            history_record=GetAttr(MetadataModule, "history")(**InputData["history"]),
            keywords_data=GetAttr(MetadataModule, "keywords")(**InputData["keywords"]),
        ),
    )
