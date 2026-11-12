from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def WideWord(TextValue: str) -> KAsmToken:
    if not TextValue.isascii():
        raise ValueError("Fusion journal program text must be ASCII")
    return (7 if len(TextValue) <= 255 else 8), TextValue
