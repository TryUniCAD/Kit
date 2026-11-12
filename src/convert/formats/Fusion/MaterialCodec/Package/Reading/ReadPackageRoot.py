from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.MaterialCodec.Package.Envelope.CheckFormats import (
    CheckFormats,
)
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxPackage,
    KMaxSchemas,
    KMaxXmlBytes,
)


def ReadPackageRoot(Archive: IndexedArchive) -> str:
    if (
        len(Archive.Entries) > KMaxSchemas + 14
        or sum(Entry.file_size for Entry in Archive.Entries.values()) > KMaxPackage
    ):
        raise ValueError("Material package index exceeds limits")
    Links = ReadLinks(Archive.ReadMember("cnx.xml", KMaxXmlBytes))
    if (
        len(Links) != 1
        or len(Links[0]) != 36
        or any(Character not in "0123456789abcdefABCDEF-" for Character in Links[0])
    ):
        raise ValueError("Material package requires one UUID asset folder")
    Prefix = Links[0] + "/"
    if ReadLinks(Archive.ReadMember(Prefix + "cnx.xml", KMaxXmlBytes)) != (
        "AssetData",
        "Schemas",
    ):
        raise ValueError("Unsupported material asset folders")
    CheckFormats(
        Archive.ReadMember("[Content_Types].xml", KMaxXmlBytes),
        Archive.ReadMember("autodesk-design-package.xml", KMaxXmlBytes),
    )
    return Prefix
