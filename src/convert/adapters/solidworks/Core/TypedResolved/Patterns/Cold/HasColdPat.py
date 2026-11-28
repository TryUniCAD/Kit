from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitResolvedStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)


# identified ordinary pattern features require typed history while raw extraction keeps its own contract
def HasColdPat(
    Archive: SldprtArchive, ModelValue: NativeModel, Settings: ReadOptions
) -> bool:
    if (
        Settings.extract_raw_brep
        or Archive.format_version != 4
        or ContainerMo(Archive.streams) != 19000
        or KitResolvedStream in Archive.streams
        or not any(
            Value.object_id > 0
            and (
                Value.class_name == "moLPattern_c"
                or (Value.xml_tag == "Feature" and Value.kind == "LPattern")
            )
            for Value in ModelValue.features
        )
    ):
        return False
    if IsCacheAbsent(Archive):
        return True
    if Settings.strict:
        raise SldprtFormat(
            "saved linear pattern lacks a verified typed feature history"
        )
    return False
