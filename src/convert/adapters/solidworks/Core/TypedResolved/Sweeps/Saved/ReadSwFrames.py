from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream


# active and delta frames must completely occupy the actual configuration partition stream
def ReadSwFrames(Archive: SldprtArchive) -> tuple[bytes, bytes]:
    RawValue = Archive.require(KPartitionStream)
    FramesValue = DecodePartData(RawValue, KPartitionStream)
    if len(FramesValue) != 2:
        raise ValueError("SOLIDWORKS saved sweep requires active and delta frames")
    Active, Deltas = FramesValue[0], FramesValue[1]
    if (
        Active.wrapper_offset != 0
        or Deltas.wrapper_offset != Active.stored_size
        or Active.stored_size + Deltas.stored_size != len(RawValue)
    ):
        raise ValueError("SOLIDWORKS saved sweep has alternate result framing")
    return Active.data, Deltas.data
