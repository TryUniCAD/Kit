from argparse import ArgumentParser
from hashlib import sha256
from math import isclose, isfinite
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import struct
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
PLAN = "fcc5eab69cfd2c45110b30232b0cb390e7cf797f9791defdecb539505b805526"
GENERATED = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
EDITED = "236865bd1e13e246199429ad635da99a737b6280802c61df252c92d613275452"
SCHEMA = "kit.sw2026.disclosed-two-stock-tolerance-observation.v1"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def pinned(path, digest):
    require(path.is_file() and not path.is_symlink(), "tolerance source is missing or redirected")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, "tolerance source digest differs")
    return raw


def worker():
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import ReadStockRoots
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName

    for name in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(name)
    blocked = []

    def audit(event, _):
        if event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn", "os.startfile"} or event.startswith(
            ("subprocess.", "socket.", "ctypes.", "winreg.")
        ):
            blocked.append(event)
            raise PermissionError("tolerance decode attempted " + event)

    sys.addaudithook(audit)
    raw = sys.stdin.buffer.read()
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    features = ReadStockRoots(link)
    _, stock1, _, stock2, _, cut = tuple(features.values())[-6:]
    output = {}
    for order, node in enumerate((stock1, stock2, cut)):
        owner = ReadExtrude(link, node, features, IsCut=order == 2, NewSolid=order == 1)
        value = node.FieldsValue["f838"]
        require(type(value) is float and isfinite(value) and value >= 0, "invalid native tolerance word")
        output[ReadNodeName(node)] = {
            "feature_id": NativeNodeId(node), "map_index": node.IndexValue,
            "class": node.ClassValue.NameValue, "f810": node.FieldsValue["f810"],
            "f2b8": node.FieldsValue.get("f2b8"), "f2bc": node.FieldsValue.get("f2bc"),
            "f838_m": value, "f838_le": struct.pack("<d", value).hex(),
            "d1_mm": owner.DepthValue.DepthValue.value_mm if owner.DepthValue is not None else None,
        }
    require(not blocked, "tolerance decode attempted external access")
    return {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "owners": output,
            "guarded_external_accesses": len(blocked)}


def prove(packet, summary):
    plan = json.loads(pinned(packet / "Plan.json", PLAN))
    report_bytes = summary.read_bytes()
    native = json.loads(report_bytes)
    require(
        native["plan_sha256"] == PLAN
        and native["schema"] == "kit.sw2026.disclosed-two-stock-save-contrast.v1"
        and native["oracle_sha256"] == plan["oracle_sha256"]
        and native["generated_sha256"] == GENERATED
        and native["held_out_sources_read"] == 0
        and set(native["records"]) == {"Before", "Unchanged", "Selected", "Reopen", "After"}
        and all(phase["passed"] for phase in native["records"].values()),
        "native contrast lacks a successful controlled lifecycle",
    )
    previous = packet.parent / "GeneratedTwoStockGraph01"
    unchanged, selected = (native["derivatives"][name] for name in ("Unchanged", "Selected"))
    inputs = {
        "generated": (previous / "GeneratedTwoStockGraph01.SLDPRT", GENERATED, (12, 10)),
        "native_moving_edit": (previous / "NativeAfterEdit.SLDPRT", EDITED, (12, 29)),
        "native_unedited": (packet / unchanged["name"], unchanged["sha256"], (12, 10)),
        "native_selected_edit": (packet / selected["name"], selected["sha256"], (18, 10)),
    }
    phases = {}
    for name, (path, digest, depths) in inputs.items():
        proc = run(
            (sys.executable, "-I", "-B", str(HERE), "--worker"),
            input=pinned(path, digest), capture_output=True, timeout=80,
        )
        require(proc.returncode == 0, proc.stderr.decode())
        phase = json.loads(proc.stdout)
        owners = phase["owners"]
        require(
            set(owners) == {"MovingStock", "SteadyStock", "ThroughFeature"}
            and owners["ThroughFeature"]["d1_mm"] is None
            and (owners["SteadyStock"]["f810"], owners["MovingStock"]["f810"], owners["ThroughFeature"]["f810"]) == (-1, 0, 1)
            and all(
                isclose(owners[key]["d1_mm"], expected, rel_tol=0, abs_tol=1e-8)
                for key, expected in zip(("SteadyStock", "MovingStock"), depths, strict=True)
            ),
            "the actual owners or D1 contrasts differ",
        )
        phases[name] = phase
    return {
        "schema": SCHEMA, "source_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
        "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "native_summary_sha256": sha256(report_bytes).hexdigest(), "native": native,
        "phases": phases, "guarded_archive_processes": len(phases),
        "held_out_cases": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.worker:
        result = worker()
    else:
        require(args.packet and args.summary, "provide the disclosed native packet and summary")
        result = prove(args.packet, args.summary)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
