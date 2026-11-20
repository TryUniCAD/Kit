# duplicate parameters or handles cannot establish a unique sketch count owner
def JoinCountPairs(Parameters, Handles, Markers):
    Results = []
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
