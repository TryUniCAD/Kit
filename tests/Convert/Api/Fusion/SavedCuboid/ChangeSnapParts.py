from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# distinct snapshot names isolate missing and excess members in the public read tests
def ChangeSnapParts(Model: DocumentModel, RoleName: str) -> DocumentModel:
    if RoleName == "missing_part":
        return ReplaceValue(Model, Snapshots=())
    if RoleName in ("part_name", "extra_part", "root_with_extra"):
        (Snapshot,) = Model.Snapshots
        Renamed = ReplaceValue(
            Snapshot,
            Name="Breps.BlobParts/BREP.01234567-89ab-cdef-0123-456789abcdef.smb",
        )
        if RoleName == "part_name":
            return ReplaceValue(Model, Snapshots=(Renamed,))
        return ReplaceValue(Model, Snapshots=(Snapshot, Renamed))
    raise ValueError("Unknown saved snapshot member mutation")
