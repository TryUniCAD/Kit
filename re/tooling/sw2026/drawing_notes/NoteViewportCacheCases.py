CORE_STREAMS = {
    "Contents/Definition",
    "Header2",
    "ModelStamps",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
    "docProps/ISolidWorksInformation.xml",
    "swXmlContents/KeyWords",
}
GRAPHICS_OMISSIONS = {
    "Repacked": (),
    "OmitDisplayLists": ("Contents/DisplayLists",),
    "OmitViewBucketLists": ("Contents/VBLists",),
    "OmitDisplayStamp": ("_DL_VERSION_19000/DLUpdateStamp",),
    "OmitAllThree": (
        "Contents/DisplayLists",
        "Contents/VBLists",
        "_DL_VERSION_19000/DLUpdateStamp",
    ),
}
CORE_BASIS_SHA256 = "d7c37d23a656c4df88bfe48446aee578d98c208f95d06fc01d035d010879e588"


def omission_cases(profile, order):
    if profile == "graphics":
        return GRAPHICS_OMISSIONS
    if profile == "seven" and len(set(order)) == len(order) == 29 and CORE_STREAMS <= set(order):
        return {"Repacked": (), "CoreSeven": tuple(name for name in order if name not in CORE_STREAMS)}
    raise ValueError("unexpected viewport cache diagnostic profile or source stream order")


def cache_basis_passed(row):
    return (row["schema"] == "kit.sw2026.disclosed-note-viewport-cache-result.v1"
            and row["distinct_processes"] == 9 and row["controls_healthy"]
            and row["diagnostic_completed"] and row["all_diagnostic_copies_match"]
            and row["matches_unchanged_annotated_source"]["OmitAllThree"]["all_exact"])
