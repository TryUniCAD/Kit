from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(HERE.parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from PatternAngleGeometry import canonical_angle_geometry
from PatternHingeGeometry import derive_hinge


def main():
    ArgumentParser().parse_args()
    request = json.load(sys.stdin)
    audit.BeginBuild()
    if type(request) is not dict or set(request) != {"plate_box_m", "raised_box_m", "angle_rad", "reverse"}:
        raise ValueError("analytic angular datum requires only explicit neutral geometry and angle intent")
    ends = derive_hinge(request["plate_box_m"], request["raised_box_m"])["ordered_endpoints_m"]
    result = canonical_angle_geometry(*ends, request["angle_rad"], reverse=request["reverse"])
    rejected = {}
    for name, supplied in (("reversed_constraint", (*ends, request["angle_rad"], True)),
                           ("crossed_endpoints", (*reversed(ends), request["angle_rad"], False)),
                           ("missing_nonzero_angle", (*ends, 0.0, False))):
        try:
            canonical_angle_geometry(*supplied[:3], reverse=supplied[3])
        except ValueError as error:
            rejected[name] = str(error)
    if len(rejected) != 3:
        raise ValueError("an unsupported angular datum bypassed the analytic boundary")
    print(json.dumps({"analytic_geometry": result, "ordered_endpoints_m": ends, "refusals": rejected,
                      "guarded_runtime_reads": len(audit.DeniedReads), "archive_written": False},
                     allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
