from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# native sidedness must retain the distinct meaning of total and per side distances
def ReadExtentMode(Feature: NativeNode) -> str:
    Fields = Feature.Fields
    Direction = Fields["directionType"]
    Measurement = Fields["symmetricMeasurementType"]
    if type(Direction) is not int or type(Measurement) is not int:
        raise ValueError("Native extrusion extent modes must be integers")
    if Direction == 3 and Measurement in (1, 2):
        return "symmetric_full" if Measurement == 1 else "symmetric_half"
    if Direction in (1, 2) and Measurement == 0:
        return "one_sided" if Direction == 1 else "two_sided"
    raise ValueError("Unsupported native Fusion extrusion extent mode")
