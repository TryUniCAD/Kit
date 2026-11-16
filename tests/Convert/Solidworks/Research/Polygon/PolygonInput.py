from __future__ import annotations

# input geometry must be authored without depending on saved vendor documents
KInput = """
Cases = {
    'crossing': ((0, 0), (3, 2), (0, 3), (2, 0)),
    'touch': ((0, 0), (3, 0), (3, 3), (1, 0), (0, 3)),
    'vertical_overlap': ((0, 0), (0, 4), (3, 4), (0, 1), (0, 3), (3, 0)),
    'backtrack': ((0, 0), (3, 0), (1, 0), (3, 3), (0, 3)),
    'collinear': ((0, 0), (1, 0), (3, 0), (3, 2), (0, 2)),
    'vertical': ((0, 0), (3, 0), (3, 1), (3, 3), (0, 3), (0, 2)),
}
Vertices = Cases.get(Scenario)
if Vertices is None:
    Vertices = tuple((CosValue(TauValue * Index / Count), SinValue(TauValue * Index / Count)) for Index in range(Count))
"""
