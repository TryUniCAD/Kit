from convert.adapters.solidworks.Container.Format import KeywordsStream

# strict blank admission must account for every stream before any diagnostics can be removed
KBlankStreamNames = (
    "Header2",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
    "Contents/Definition",
    "ModelStamps",
    KeywordsStream,
    "docProps/ISolidWorksInformation.xml",
)
