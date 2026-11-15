from __future__ import annotations

from Schema import Registry

from convert.adapters.solidworks.container.Container import SldprtArchive
from tests.convert.solidworks.research.Composition.ProfileRoots import ReadProfiles


# complete file decoding must preserve exclusive reference allocations and their shared model relationship
def ReadOwners(ArchiveFile: SldprtArchive, CodecReg: Registry) -> dict[str, bool]:
    ModelRoot, Profiles = ReadProfiles(ArchiveFile, CodecReg)
    if len(Profiles) != 2:
        raise RuntimeError("constructed part requires origin and ordinary profiles")
    OriginRef, SketchRef = [Profile["pd_f78"] for Profile in Profiles]
    Components = [OriginRef["f58"], SketchRef["f58"]]
    return {
        "distinct_wrappers": OriginRef is not SketchRef,
        "distinct_components": Components[0] is not Components[1],
        "copied_components": all(
            Component is not ModelRoot["f990"] for Component in Components
        ),
        "shared_model_owner": all(
            Component["owner"] is ModelRoot for Component in Components
        ),
        "same_plane": OriginRef["ff0"] == SketchRef["ff0"],
    }
