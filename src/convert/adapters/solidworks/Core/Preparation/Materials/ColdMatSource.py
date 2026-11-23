from convert.adapters.solidworks.Container.Format import KPartFormatId
from interchange.Records.RecordSource import CadSource

# the material source tag binds this decoded design to its actual native locator and epoch
KColdMatSource = "cold_material_model"


# this cache free design requires a typed decoder and exact source ownership
def IsColdMatSource(SourceValue: CadSource) -> bool:
    return (
        SourceValue.format_id == KPartFormatId
        and SourceValue.container_version == "4"
        and SourceValue.attributes.get(KColdMatSource) is True
    )
