from pathlib import Path
import sys

from AuthorCurves import require
from AuthorEqualLengthRevolves import EqualLengthAuthor
from InspectGeneratedRevolveEnds import FullRevolveEndObserver

sys.path.insert(0, str(Path(__file__).resolve().parent / "revolve" / "EndModes"))
from SquareEdgeRoles import contour_roles, edge_role


class FullSquareObserver(FullRevolveEndObserver, EqualLengthAuthor):
    relation_count = 5

    def snapshot(self, case, label, angle_degrees):
        feature = super().snapshot(case, label, angle_degrees)
        roles = contour_roles(case)
        owners = {tuple(row["id"]): edge_role(roles, (row["start"], row["end"]))
                  for row in self.geometry() if not row["construction"]}
        require(len(owners) == 4 and set(owners.values()) == set(range(4)), "revolve contour roles are incomplete")
        relations = self.rec.data[label]["relations"]
        operands = sorted([row["code"], [owners[tuple(owner["id"])] for owner in row["owners"]]] for row in relations)
        require({tuple(row[1]) for row in operands if row[0] != 14} == {(0,), (1,), (2,), (3,)},
                "native unary operands do not cover the actual contour")
        self.rec.data[label]["relation_operands"] = operands
        self.rec.flush()
        return feature
