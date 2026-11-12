from re import fullmatch as FullMatch


def IsGraphicPath(NameValue: str) -> bool:
    return (
        FullMatch(
            r"OGS\.BlobFolder/OGS/DefaultScene/(world|stream_mesh_[0-9]{3})", NameValue
        )
        is not None
    )
