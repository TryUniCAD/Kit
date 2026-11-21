from __future__ import annotations

import json
import sys

from CoincidentMateBundleProcess import generated_mate_report


def main():
    print(json.dumps(generated_mate_report(json.load(sys.stdin), kind="parallel"), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
