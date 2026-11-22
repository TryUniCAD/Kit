from tests.Convert.Solidworks.KeywordModels.RunKeywordModel import ReadKeyModel

# independent markup distinguishes ordered owners and the two cut dimension forms
KPositionalWire = (
    b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n'
    + (
        '<Keywords id="1423956721" Name="Modulo λ &amp; &quot;edge&quot; &lt;&gt;">'
        '<Configuration id="33" Name="β transient" Type="ConfigurationManager" Material="" />'
        '<Configuration id="4" Name="α stock" Type="ConfigurationManager" Material="" />'
        '<Feature id="33" Name="Parent plane" Type="moRefPlane_c" />'
        '<Sketch id="21" Name="Pocket λ" Type="moProfileFeature_c">'
        '<Dimension Name="Width">19</Dimension>'
        '<Dimension Name="Height">0.10000000000000001</Dimension>'
        "</Sketch>"
        '<Extrusion id="144" Name="Blind cut" DissectableChildren="21">'
        '<Dimension Name="D1">6.125</Dimension></Extrusion>'
        '<Sketch id="8" Name="Tunnel outline" Type="moProfileFeature_c" />'
        '<Extrusion id="3" Name="Through cut" DissectableChildren="8" />'
        "</Keywords>"
    ).encode("utf-8")
    + b"\r\n"
)


# deliberately unordered identifiers prove output follows model order within each namespace
def MakeLinearKeys() -> dict[str, object]:
    return {
        "name": 'Modulo λ & "edge" <>',
        "timestamp": 1423956721,
        "configurations": [
            {"id": 33, "name": "β transient", "material": ""},
            {"id": 4, "name": "α stock", "material": ""},
        ],
        "features": [
            {
                "id": 33,
                "name": "Parent plane",
                "kind": "moRefPlane_c",
                "tag": "Feature",
            },
            {
                "id": 21,
                "name": "Pocket λ",
                "kind": "moProfileFeature_c",
                "tag": "Sketch",
                "dimensions": [
                    {"name": "Width", "value": 19},
                    {"name": "Height", "value": 0.1},
                ],
            },
            {
                "id": 144,
                "name": "Blind cut",
                "kind": None,
                "tag": "Extrusion",
                "children": [21],
                "dimensions": [{"name": "D1", "value": 6.125}],
            },
            {
                "id": 8,
                "name": "Tunnel outline",
                "kind": "moProfileFeature_c",
                "tag": "Sketch",
            },
            {
                "id": 3,
                "name": "Through cut",
                "kind": None,
                "tag": "Extrusion",
                "children": [8],
            },
        ],
    }


# parse the emitted index independently to verify dimension ownership and absent depth
def TestLinearKeys() -> None:
    Report = ReadKeyModel(MakeLinearKeys(), KPositionalWire)
    assert Report["root"] == ["Keywords", "1423956721", 'Modulo λ & "edge" <>']
    assert Report["order"] == [
        ["Configuration", "33", "β transient"],
        ["Configuration", "4", "α stock"],
        ["Feature", "33", "Parent plane"],
        ["Sketch", "21", "Pocket λ"],
        ["Extrusion", "144", "Blind cut"],
        ["Sketch", "8", "Tunnel outline"],
        ["Extrusion", "3", "Through cut"],
    ]
    assert Report["children"] == [["144", "21"], ["3", "8"]]
    assert Report["dimensions"] == [
        ["21", [["Width", "19"], ["Height", "0.10000000000000001"]]],
        ["144", [["D1", "6.125"]]],
    ]
