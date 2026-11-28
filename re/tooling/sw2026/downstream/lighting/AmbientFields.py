from downstream.lighting.AmbientInput import (
    AmbientInput,
)


# the concrete type one constructor initializes every serialized light tail before explicit coefficient setters
def AmbientFields(InputValue: AmbientInput) -> dict[str, object]:
    return {
        "f35c": 0,
        "f0c": 0,
        "f390": InputValue.AmbientValue,
        "f398": InputValue.DiffuseValue,
        "f3a0": InputValue.SpecularValue,
        "f3a8": InputValue.ColourValue,
        "state": 0,
        "f428": 1,
        "f36c": 0,
        "f4f0": 1,
        "f4f8": InputValue.ExternalName,
        "f384#0": 0,
        "f384": 0,
        "f388": 1,
        "f478": 1.0,
        "f488": 1,
        "f490": 16.0,
        "f500": {"n": 0, "props": []},
    }
