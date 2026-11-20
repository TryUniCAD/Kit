from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import InspectSdkCircleHeldouts as observer


def main():
    curve = observer.AuthorCurves.CurveAuthor
    original_tree = curve.feature_tree

    def retain_tree(self, **options):
        rows = original_tree(self, **options)
        self.rec.data.setdefault("complete_tree_observations", []).append(rows)
        self.rec.flush()
        return rows

    curve.feature_tree = retain_tree
    try:
        return observer.main()
    finally:
        curve.feature_tree = original_tree


if __name__ == "__main__":
    raise SystemExit(main())
