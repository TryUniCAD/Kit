from types import MappingProxyType

# differing authored contours force archive lengths and allocator maps to follow the model rather than a fixed saved shape
KContours = MappingProxyType(
    {
        "x": [[0.0, 0.0], [0.0317, 0.0], [0.0317, 0.0126], [0.0, 0.0126]],
        "y": [[0.0, 0.0], [0.0173, 0.0], [0.0, 0.0239]],
        "z": [
            [0.0, 0.0],
            [0.0261, 0.0],
            [0.0329, 0.0083],
            [0.0147, 0.0241],
            [0.0, 0.0157],
        ],
    }
)

# every endpoint selects a real child datum by its independently authored principal plane role
KDatumNames = MappingProxyType(
    {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}
)
