from __future__ import annotations

from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.Composition.NodeFields import ReadFields
from tests.Convert.Solidworks.Research.Composition.ProfileRoots import ReadProfiles


# complete file decoding must preserve exclusive reference allocations and their shared model relationship
def ReadOwners(ArchiveFile: SldprtArchive, CodecReg: object) -> dict[str, bool]:
    ModelRoot, Profiles = ReadProfiles(ArchiveFile, CodecReg)
    if len(Profiles) != 2:
        raise RuntimeError("constructed part requires origin and ordinary profiles")
    OriginRef, SketchRef = [ReadFields(Profile)["pd_f78"] for Profile in Profiles]
    OriginFields, SketchFields = ReadFields(OriginRef), ReadFields(SketchRef)
    Components = [OriginFields["f58"], SketchFields["f58"]]
    return {
        "model_visual_properties": getattr(ReadFields(ModelRoot)["f78"], "cls", None)
        == "moVisualProperties_c",
        "separate_visual_owners": all(
            ReadFields(Profile)["f78"] is not ReadFields(ModelRoot)["f78"]
            for Profile in Profiles
        ),
        "distinct_wrappers": OriginRef is not SketchRef,
        "distinct_components": Components[0] is not Components[1],
        "copied_components": all(
            Component is not ReadFields(ModelRoot)["f990"] for Component in Components
        ),
        "shared_model_owner": all(
            ReadFields(Component)["owner"] is ModelRoot for Component in Components
        ),
        "same_plane": OriginFields["ff0"] == SketchFields["ff0"],
    }
