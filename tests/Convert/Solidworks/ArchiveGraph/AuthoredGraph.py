# source names identify distinct nodes locally before any archive slot is assigned
def AuthoredGraph() -> dict[str, object]:
    return {
        "primary": "root",
        "linked": "child",
        "nodes": {
            "root": {
                "class": ["Root", 1],
                "value": 11,
                "links": ["leaf", "leaf", "twin", "root"],
            },
            "leaf": {"class": ["Leaf", 2], "value": 29, "links": ["root", None]},
            "twin": {"class": ["Leaf", 2], "value": 29, "links": ["root", None]},
            "child": {
                "class": ["Leaf", 2],
                "value": 41,
                "links": ["leaf", "root", "child"],
            },
        },
    }
