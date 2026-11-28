from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CoincidentMateBundleProcess import generated_mate_report
from PlanarMateEndpointProcess import require


def main():
    report = generated_mate_report(json.load(sys.stdin), kind="distance")
    require(report["input_runtime_file_access_attempts"] == 0, "distance construction attempted runtime file access")
    report["split"] = "discovery"
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
