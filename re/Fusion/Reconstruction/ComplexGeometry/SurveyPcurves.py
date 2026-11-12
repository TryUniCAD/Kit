import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import SubtypeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402


def main():
    data = json.loads((BASE / "VerifyComplex.json").read_text())
    stats = collections.Counter()
    for member in data["members"]:
        if member["status"] != "exact":
            continue
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            payload = archive.read(member["member"])
        model = ReadJournal(payload) if member["member"].endswith(".smbh") else ReadGeometry(payload)
        entities = model.Entities
        for value in entities:
            if not isinstance(value, CoedgeNode) or value.PcurveRef < 0:
                continue
            pcurve = entities[value.PcurveRef]
            edge = entities[value.EdgeRef]
            if not isinstance(pcurve, PcurveNode):
                stats["notpcurve"] += 1
                continue
            key = [f"coedgeRev={value.Reversed}", f"form={pcurve.Form}", f"pcRev={pcurve.Reversed}", f"partner={value.Partner >= 0}"]
            if pcurve.Form == 0 and isinstance(pcurve.Carrier, SubtypeNode):
                curve = pcurve.Carrier.Body[0]
                lower, upper = curve.Knots[0], curve.Knots[-1]
                if abs(lower - edge.StartParam) < 1e-9 and abs(upper - edge.EndParam) < 1e-9:
                    key.append("range=edge")
                elif abs(lower + edge.EndParam) < 1e-9 and abs(upper + edge.StartParam) < 1e-9:
                    key.append("range=negated")
                else:
                    key.append("range=other")
                key.append(f"offsets={pcurve.UOffset != 0 or pcurve.VOffset != 0}")
            stats[" ".join(key)] += 1
    for key, count in stats.most_common():
        print(count, key)


main()
