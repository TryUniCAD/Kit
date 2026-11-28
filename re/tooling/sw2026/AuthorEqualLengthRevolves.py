from collections import Counter
from pathlib import Path

from AuthorCurves import require
from AuthorRevolveEnds import main
from InspectRevolveRelations import RelationObserver, constraint_codes


class EqualLengthAuthor(RelationObserver):
    def snapshot(self, case, label, angle_degrees):
        feature = super().snapshot(case, label, angle_degrees)
        rows = self.rec.data[label]["relations"]
        inventory = Counter(entry["name"] for entry in rows)
        require(inventory == {
            "swConstraintType_SAMELENGTH": 1,
            "swConstraintType_HORIZONTAL": 2,
            "swConstraintType_VERTICAL": 2,
        }, "native square contour does not have the complete equal length relation")
        pair, = (entry["owners"] for entry in rows if entry["name"] == "swConstraintType_SAMELENGTH")
        require(len(pair) == 2 and pair[0]["id"] != pair[1]["id"]
                and all(owner["kind"] == 0 and not owner["construction"] for owner in pair),
                "equal length relation is missing its distinct live contour lines")
        return feature


if __name__ == "__main__":
    EqualLengthAuthor.codes = constraint_codes()
    source = Path(__file__)
    raise SystemExit(main(EqualLengthAuthor, (source, source.with_name("InspectRevolveRelations.py"))))
