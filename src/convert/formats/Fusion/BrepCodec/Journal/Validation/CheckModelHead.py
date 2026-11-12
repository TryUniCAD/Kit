from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader


def CheckModelHead(Header: BrepHeader, HasHistory: bool) -> None:
    if type(Header.RootCount) is not int or not 2 <= Header.RootCount <= 129:
        raise ValueError("Fusion geometry body-root count exceeds its quota")
    Expected = BrepHeader(
        23200,
        Header.RootCount,
        3 if HasHistory else 2,
        50.0 if HasHistory else 10.0,
        1e-6,
        1e-10,
    )
    if Header != Expected:
        raise ValueError("Unsupported Fusion geometry header profile")
