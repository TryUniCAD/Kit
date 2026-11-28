from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase

# independent capture dimensions prevent one measured source from qualifying the entire saved cohort
KSavedCases = (
    SavedCase(
        "BaselineControl.f3d",
        "5f9ad382c5e4b15313a59bebe4201ccd5b87137a3f20ebe85f5e3fba79148ca0",
        16.4,
        27.1,
        13.8,
    ),
    SavedCase(
        "BaselineEdited.f3d",
        "1e7584c59f898b41af2ea3d5accf0c5c44e793bcd0ab7c5486a08feb55443aa2",
        16.4,
        27.1,
        28.3,
    ),
    SavedCase(
        "BaselineRestored.f3d",
        "b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752",
        16.4,
        27.1,
        13.8,
    ),
    SavedCase(
        "HoldoutControl.f3d",
        "850b1a76c30c673ba10e33ef1e78618c5e9f106646d5aa9fbf3411ddd6683ac4",
        43.7,
        12.9,
        31.4,
    ),
)
