from convert.adapters.solidworks.Container.Format import KPartFormatId
from interchange.Records.RecordSource import CadSource

# the portable source distinguishes analytic cold geometry from an actual saved result partition
KColdSweepSource = "cold_sweep_model"


# only the typed cold source profile can request measured sweep republication
def IsColdSwSource(SourceValue: CadSource) -> bool:
    return (
        SourceValue.format_id == KPartFormatId
        and SourceValue.container_version == "4"
        and SourceValue.attributes.get(KColdSweepSource) is True
    )
