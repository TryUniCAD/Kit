from argparse import ArgumentParser
from base64 import b64encode
import json
from math import isfinite
from pathlib import Path, PureWindowsPath
import re
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditColdSweep import EPOCH, guard_runtime, inspect_output
from MakeColdSweepPart import make_cold_sweep_part
from SweepModel import require


def produce(request):
    require(set(request) == {"name", "section_radius_m", "path_radius_m", "density_kg_m3", "self_locator"},
            "the model-only producer accepts only initial neutral geometry, density and target identity")
    name, locator = request["name"], request["self_locator"]
    target = PureWindowsPath(locator)
    require(re.fullmatch("Slot0[12]|SweepArcNear|SweepArcWide", name) is not None
            and target.is_absolute() and target.drive.casefold() == "c:" and ".." not in target.parts
            and target.name == name + ".SLDPRT", "unbound candidate self locator")
    radii = request["section_radius_m"], request["path_radius_m"]
    density = request["density_kg_m3"]
    require(type(density) in (int, float) and isfinite(density) and density > 0, "invalid neutral density")
    blocked = guard_runtime()
    args = name, *radii, density, EPOCH, locator
    part = make_cold_sweep_part(*args)
    require(part[0] == make_cold_sweep_part(*args)[0], "generated part is not deterministic")
    checked = inspect_output(*part, radii)
    require(not blocked, "model-only sweep accessed an external runtime source")
    return {"part": b64encode(part[0]).decode("ascii"), "candidate_sha256": checked["candidate_sha256"],
            "stream_count": len(checked["stream_sha256"]), "exact_replays": len(checked["exact_stream_replays"]),
            "blocked_runtime_calls": len(blocked)}


def main():
    parser = ArgumentParser()
    parser.add_argument("--closure", action="store_true")
    if parser.parse_args().closure:
        root = HERE.parents[3]
        paths = {path.relative_to(root).as_posix() for module in tuple(sys.modules.values())
                 if (member := getattr(module, "__file__", None))
                 and (path := Path(member).resolve()).is_relative_to(root / "re" / "tooling")}
        print(json.dumps(sorted(paths)))
    else:
        result = produce(json.load(sys.stdin))
        print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
