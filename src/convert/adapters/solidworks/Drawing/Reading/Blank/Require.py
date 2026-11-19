from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# unrepresented blank owners must fail before a complete semantic projection can be returned
def Require(Value: object, Label: str) -> None:
    if not Value:
        raise BodyUnsupported(Label)
