from json import loads
from pathlib import PureWindowsPath
from re import fullmatch

from FilletModel import require, validate_cases
from FilletPacket import CONTROL, SHARED_TOOLS
from FilletStockPacket import INTENT_SHA, NAMES, ORACLE_AUTHORITY, pinned

SCHEMA = "kit.sw2026.edge-fillet-model-job.v1"
OWNED_TOOLS = (
    "FilletModel.py", "FilletModelPacket.py", "FilletPacket.py", "FilletStockPacket.py",
    "FilletSourcePhase.py", "FilletAuthor.py", "FilletApi.py", "RunModelFillet.py",
)
FILES = {
    "Spec.json", "Control.SLDPRT", "Construction.json",
    *(f"Generated/{name}.SLDPRT" for name in NAMES),
    *(f"Tool/{name}" for name in (*SHARED_TOOLS, *OWNED_TOOLS)),
}


def root_value(value):
    require(type(value) is str and fullmatch(r"C:\\KitEdgeFilletModelCold[0-9]{2}", value),
            "fillet model batch needs a fresh numbered local Windows root")
    return PureWindowsPath(value)


def locator(root, name):
    require(name in NAMES, "unexpected model fillet name")
    return str(root / "Candidates" / f"{name}.SLDPRT")


def generation_cases(proof, root, commit, tree):
    cases = proof["cases"]
    require(proof["schema"] == "kit.sw2026.edge-fillet-model-cold.v1"
            and proof["source_head"] == commit and proof["source_tree_at_head"] == tree
            and proof["neutral_intent_sha256"] == INTENT_SHA
            and proof["encoded_guest_root"] == str(root)
            and proof["fresh_guarded_processes"] >= 4 and proof["host_native_launches"] == 0
            and set(cases) == set(NAMES), "generation proof does not bind the writer and both cases")
    for name, row in cases.items():
        require(row["guarded_external_accesses"] == 0 and row["encoded_locator"] == locator(root, name)
                and fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                f"no matching guarded model-only construction for {name}")
    return cases


def load_job(path, pin):
    require(path.name == "ModelJob.json" and fullmatch(r"[0-9a-f]{64}", pin),
            "model fillet packet requires its exact manifest hash")
    folder = path.parent.resolve()
    job = loads(pinned(folder / path.name, pin))
    root = root_value(job["guest_root"])
    require(job["schema"] == SCHEMA and job["oracle"] == ORACLE_AUTHORITY
            and fullmatch(r"[0-9a-f]{40}", job["writer_commit"])
            and fullmatch(r"[0-9a-f]{40}", job["writer_tree"])
            and fullmatch(r"[0-9a-f]{40}", job["probe_commit"])
            and set(job["files"]) == FILES, "model fillet packet authority differs")
    require({item.relative_to(folder).as_posix() for item in folder.rglob("*")}
            == FILES | {path.name, "Generated", "Tool"},
            "model fillet packet contains an unbound file")
    require(job["files"]["Control.SLDPRT"]["sha256"] == CONTROL
            and job["files"]["Spec.json"]["sha256"] == INTENT_SHA,
            "model fillet batch changed its inputs or healthy control")
    for name, row in job["files"].items():
        raw = pinned(folder / name, row["sha256"])
        require(len(raw) == row["bytes"], f"model fillet packet size differs: {name}")
    cases = validate_cases(loads(pinned(folder / "Spec.json", INTENT_SHA)))
    require(tuple(case["name"] for case in cases) == NAMES, "unexpected model fillet cases")
    proof = loads((folder / "Construction.json").read_bytes())
    for name, generated in generation_cases(proof, root, job["writer_commit"], job["writer_tree"]).items():
        expected = job["files"][f"Generated/{name}.SLDPRT"]
        require(generated["sha256"] == expected["sha256"] and generated["bytes"] == expected["bytes"],
                f"transport changed the model-only construction for {name}")
    return folder, root, job, {case["name"]: case for case in cases}
