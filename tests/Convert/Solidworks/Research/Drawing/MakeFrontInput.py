from tests.Convert.Solidworks.Research.Drawing.MakeSheetInput import MakeSheetInput
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# independent child dimensions must corroborate drawing emission through the public reader
def MakeFrontInput(
    Label: str, Width: float, Height: float, Depth: float
) -> dict[str, object]:
    Vertices = [
        [0.002, -0.003],
        [0.002 + Width, -0.003],
        [0.002 + Width, -0.003 + Height],
        [0.002, -0.003 + Height],
    ]
    Child = MakePartInput(Vertices, Depth, Label + "Model")
    Child["output"] = {
        "path_name": "C:\\Users\\Public\\Documents\\KitOracle\\SdkSheet\\"
        + Label
        + "Model.SLDPRT",
        "saved_at": 1794700291,
    }
    return {
        "drawing": MakeSheetInput(Label, 3, 2),
        "part": Child,
        "view": {
            "name": "Drawing View1",
            "orientation": "*Front",
            "position": [0.12413, 0.09137],
            "scale": 1.0,
            "supports": {
                "detail": "Detail Folder2",
                "sheet_plane": "Plane2",
                "sheet_profile": "Sketch2",
                "model_plane": "Plane3",
                "model_profile": "Sketch3",
            },
        },
    }
