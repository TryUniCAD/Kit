from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import BossEndInput
from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import AddCircDimMut
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import MakeCircleFeat
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import CirclePlan
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Container.Container import SldprtArchive
from SdkNativeRoundTrips import roundtrips

codecs = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
request = json.load(sys.stdin)
audit.BeginBuild()
mode = request["mode"]
end = BossEndInput(0.01931, True, 19000, mode, 0.00783 if mode == "two_directions" else None)
circle = CircleInput((0.00313, -0.00271), 0.00679, 19000)
plan = CirclePlan("LegacyEnd" + mode.replace("_", ""), "Default", "Front Plane", "z", "sketch", "CircleProfile", "boss", "BossFeature", "depth", "body", circle, "radial", False, (0.01671, 0.00408), end)
settings = MakePartRecipe(plan, 1795000000)
allocator = PersistentIds()
system = MakePartBaseMut(settings, plan, allocator)
profile = MakeCircleFeat(plan.SketchName, system.RootValue, system.SystemValues.PlaneValues["z"], "z", circle, settings.TargetValue, allocator)
radial = AddCircDimMut(profile, plan.TextPoint, False, settings.DesignIntent, settings.SelectedLeader, allocator)
candidate = FinishBlindMut(system, profile, settings, plan, allocator, MakeSketchKeys((radial,), settings.DocumentUnits.LengthUnit))
_, _, _, _, streams = roundtrips(SldprtArchive.from_bytes(candidate.BytesValue), False)
assert not audit.DeniedReads
print(json.dumps({"passed": True, "mode": mode, "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "streams": streams, "runtime_input_file_reads": 0}, sort_keys=True, allow_nan=False))
