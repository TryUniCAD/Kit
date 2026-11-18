from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemExtras,
    KSystemFolders,
)

# header intent accepts only independently mapped ordinary part and feature owners with proven persistent identities
KRevisionKinds = (
    KSystemFolders
    | KSystemExtras
    | frozenset(
        (
            "moPart_c",
            "moProfileFeature_c",
            "moExtrusion_c",
            "moRevolution_c",
            "moNotesAreaFtrFolder_c",
            "moAmbientLight_c",
            "moDirectionLight_c",
        )
    )
)
