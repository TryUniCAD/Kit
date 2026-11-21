# reconstructed geometry needs a precise public diagnostic without changing existing family messages
def ReadGeomMessage(MethodValue: str) -> str:
    Messages = {
        "typed_parametric_blind_circular_pocket": "B-rep reconstructed from the typed rectangular boss and blind circular cut",
        "typed_parametric_through_all_circular_cut": "B-rep reconstructed from the typed rectangular stock and through-all circular cut",
        "typed_parametric_selected_two_stock_cut": "B-rep reconstructed from two typed rectangular stocks and the selected circular through cut",
        "typed_parametric_selected_revolve_cut": "B-rep reconstructed from two typed annular stocks and the selected partial revolve cut",
        "typed_parametric_ordinary_revolve": "B-rep reconstructed from the typed rectangle, selected revolve axis and live angle",
        "typed_parametric_circular_boss": "B-rep reconstructed from the complete typed circular boss history",
    }
    return Messages.get(
        MethodValue,
        "B-rep reconstructed from the complete typed ordinary rectangular prism history",
    )
