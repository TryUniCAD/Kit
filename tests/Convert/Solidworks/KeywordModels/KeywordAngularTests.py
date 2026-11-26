from tests.Convert.Solidworks.KeywordModels.RunKeywordModel import ReadKeyModel

# angular framing must retain native degree text and the consumed sketch type omission
KAngularWire = (
    b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n'
    + (
        '<Keywords id="1423956722" Name="Angulaire &amp; σ">'
        '<Configuration id="2" Name="Angular profile" Type="ConfigurationManager" Material=""/>'
        '<Sketch id="55" Name="Meridian" Dissectable="true"/>'
        '<Feature id="11" Name="Revolve δ" Type="Revolve">'
        '<Dimension Name="D1">147.5°</Dimension></Feature></Keywords>'
    ).encode("utf-8")
    + b"\r\n"
)


# the degree suffix must select compact framing and recover its actual feature owner
def TestAngularKeys() -> None:
    InputValue: dict[str, object] = {
        "name": "Angulaire & σ",
        "timestamp": 1423956722,
        "configurations": [{"id": 2, "name": "Angular profile", "material": ""}],
        "features": [
            {
                "id": 55,
                "name": "Meridian",
                "kind": None,
                "tag": "Sketch",
                "dissectable": True,
            },
            {
                "id": 11,
                "name": "Revolve δ",
                "kind": "Revolve",
                "tag": "Feature",
                "dimensions": [{"name": "D1", "value": 147.5, "unit": "degree"}],
            },
        ],
    }
    Report = ReadKeyModel(InputValue, KAngularWire)
    assert Report["types"] == ["ConfigurationManager", None, "Revolve"]
    assert Report["dissectable"] == [["55", "true"]]
    assert Report["dimensions"] == [["11", [["D1", "147.5°"]]]]
