from collections.abc import Mapping


# duplicate parameters or handles cannot establish a unique sketch count owner
def JoinCountPairs(
    Parameters: Mapping[tuple[int, str], list[tuple[int, str, int]]],
    Handles: Mapping[tuple[int, str], list[tuple[int, int, int]]],
    Markers: list[tuple[int, int]],
) -> list[tuple[int, str, str, int, int, int, int, int]]:
    Results: list[tuple[int, str, str, int, int, int, int, int]] = []
    for (Marker, KindName), Items in Parameters.items():
        Family = "Circular" if KindName == "sgCircularPattCntDim" else "Linear"
        Copies = Handles.get((Marker, "moSkDimHandle" + Family + "PattCnt_c"), [])
        if len(Items) != 1 or len(Copies) != 1:
            continue
        Start, ParamName, Scalar = Items[0]
        Handle, Cursor, EndOffset = Copies[0]
        if Scalar + 8 <= Handle:
            Results.append(
                (
                    Markers[Marker][1],
                    ParamName,
                    Family.lower(),
                    Start,
                    Scalar,
                    Handle,
                    Cursor,
                    EndOffset,
                )
            )
    return Results
