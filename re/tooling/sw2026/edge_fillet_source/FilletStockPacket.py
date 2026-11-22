from hashlib import sha256
from json import loads
from pathlib import Path, PureWindowsPath
from re import fullmatch

from FilletModel import require, validate_cases
from FilletPacket import BUILD, CONTROL, ORACLE, SHARED_TOOLS

SCHEMA = "kit.sw2026.edge-fillet-stock-job.v1"
EPOCH = 1795510277
INTENT_SHA = "d985611e397e943860b8b0ce4b3f9631e6c31f5355bdd784519a2b028a9a51cb"
REGISTERED_API = "f8bc14e15ee1607deda2a3a2b76e33d7448ed522232e53268286b4da6a25e6d4"
ORACLE_AUTHORITY = {"build": BUILD, "sha256": ORACLE, "registered_api_sha256": REGISTERED_API}
NAMES = ("EdgeFilletAxial", "EdgeFilletTransverse")
PHASES = ("ControlBefore", *NAMES, "ControlAfter")
OWNED_TOOLS = ("FilletApi.py", "FilletAuthor.py", "FilletModel.py", "FilletPacket.py",
               "FilletSourcePhase.py", "FilletStockPacket.py", "RunFilletStock.py")
FILES = {"Spec.json", "Control.SLDPRT", *(f"Stock/{name}.SLDPRT" for name in NAMES),
         *(f"Tool/{name}" for name in (*SHARED_TOOLS, *OWNED_TOOLS))}


def sha(raw):
    return sha256(raw).hexdigest()


def pinned(path, pin):
    require(path.is_file() and path.resolve() == path and not path.is_symlink(),
            f"stock packet requires an ordinary direct file: {path.name}")
    raw = path.read_bytes()
    require(sha(raw) == pin, f"stock packet hash differs: {path.name}")
    return raw


def write_new(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def guest_root(value):
    require(type(value) is str and fullmatch(r"C:\\KitEdgeFilletStock[0-9]{2}", value),
            "stock job requires a fresh numbered local Windows root")
    return PureWindowsPath(value)


def stock_target(root, name):
    require(name in NAMES, "unexpected stock target name")
    return str(root / "Candidates" / f"{name}.SLDPRT")


def load_job(path, expected):
    path = path.absolute()
    require(path.name == "StockJob.json" and fullmatch(r"[a-f0-9]{64}", expected),
            "expected the exact stock packet job and digest")
    folder = path.parent
    job = loads(pinned(path, expected))
    root = guest_root(job["guest_root"])
    require(job["schema"] == SCHEMA and job["oracle"] == ORACLE_AUTHORITY and job["written_at"] == EPOCH
            and job["scope"] == "two disclosed model-only blind stocks" and job["fillet_writer_output_count"] == 0
            and fullmatch(r"[a-f0-9]{40}", job["tool_revision"])
            and fullmatch(r"[a-f0-9]{40}", job["sdk_tree"]), "stock packet policy differs")
    found = {item.relative_to(folder).as_posix(): item for item in folder.rglob("*")}
    require(set(found) == FILES | {path.name, "Tool", "Stock"} and set(job["files"]) == FILES,
            "stock packet inventory differs")
    require(all(item.resolve() == item and not item.is_symlink() for item in found.values()),
            "stock packet has an indirect child path")
    require(job["files"]["Control.SLDPRT"]["sha256"] == CONTROL
            and job["files"]["Spec.json"]["sha256"] == INTENT_SHA,
            "stock packet lost its disclosed intent or control")
    for name, entry in job["files"].items():
        raw = pinned(folder / name, entry["sha256"])
        require(len(raw) == entry["bytes"], f"stock packet size differs: {name}")
    cases = validate_cases(loads(pinned(folder / "Spec.json", INTENT_SHA)))
    require(tuple(case["name"] for case in cases) == NAMES and set(job["construction"]) == set(NAMES),
            "unexpected stock names")
    for name in NAMES:
        built = job["construction"][name]
        item = job["files"][f"Stock/{name}.SLDPRT"]
        require(built == {"encoded_locator": stock_target(root, name), "sha256": item["sha256"],
                          "logical_streams": 10, "guarded_external_accesses": 0},
                f"guarded neutral generation witness differs: {name}")
    return job, folder, root, {case["name"]: case for case in cases}
