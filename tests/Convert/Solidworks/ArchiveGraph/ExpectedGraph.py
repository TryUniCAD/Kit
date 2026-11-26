# distinct and shared graph nodes must resolve to their respective slots after reading
def ExpectedGraph() -> dict[str, object]:
    return {
        "primary": {"root": 2, "next": 6, "slots": [1, 2, 3, 4, 5]},
        "linked": {"root": 6, "base": 6, "next": 7},
        "classes": [[1, "Root", 1], [3, "Leaf", 2]],
        "objects": [
            [2, "Root", 11, [4, 4, 5, 2]],
            [4, "Leaf", 29, [2, None]],
            [5, "Leaf", 29, [2, None]],
            [6, "Leaf", 41, [4, 2, 6]],
        ],
    }
