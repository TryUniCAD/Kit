from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream


# active and delta frames must completely occupy the actual configuration partition stream
def ReadSwFrames(Archive: SldprtArchive) -> tuple[bytes, bytes]:
    RawValue = Archive.require(KPartitionStream)
    Active, Deltas = DecodePartData(RawValue, KPartitionStream)
    if (
        Active.wrapper_offset != 0
        or Deltas.wrapper_offset != Active.stored_size
        or Active.stored_size + Deltas.stored_size != len(RawValue)
    ):
        raise ValueError("SOLIDWORKS saved sweep has alternate result framing")
    return Active.data, Deltas.data
