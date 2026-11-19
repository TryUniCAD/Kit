from hashlib import sha256
import json
from math import gcd
import os
from pathlib import Path
import secrets

SLOTS = ("Slot01", "Slot02")


def require(value, message):
    if not value:
        raise ValueError(message)


def fingerprint(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def ratio(enlarged):
    while True:
        first, second = secrets.randbelow(46) + 2, secrets.randbelow(46) + 2
        if gcd(first, second) == 1 and (first > second) == enlarged:
            return [first, second]


def seal(directory, slot):
    require(
        os.name == "nt" and slot in SLOTS, "private source sealing requires the guest"
    )
    require(not directory.exists(), "private slot already exists")
    enlarged = slot == "Slot02"
    value = {
        "schema": "kit.sw2026.blank-drawing-private-intent.v1",
        "slot": slot,
        "sheet_id": "sheet-1",
        "sheet_name": "PrivateSheet" + secrets.token_hex(8),
        "width_m": 11 * 0.0254,
        "height_m": 8.5 * 0.0254,
        "scale_ratio": ratio(enlarged),
        "edit_scale_ratio": ratio(not enlarged),
        "views": [],
        "model_refs": [],
        "custody_nonce": secrets.token_hex(16),
    }
    write_new(directory / "Intent.json", value)
    return fingerprint(directory / "Intent.json")


def read_intent(directory, expected, slot):
    require(os.name == "nt", "source intents stay inside the guest")
    path = directory / "Intent.json"
    require(
        fingerprint(path) == expected and not path.is_symlink(),
        "private intent identity differs",
    )
    value = json.loads(path.read_bytes())
    require(
        set(value)
        == {
            "schema",
            "slot",
            "sheet_id",
            "sheet_name",
            "width_m",
            "height_m",
            "scale_ratio",
            "edit_scale_ratio",
            "views",
            "model_refs",
            "custody_nonce",
        }
        and value["schema"] == "kit.sw2026.blank-drawing-private-intent.v1"
        and value["slot"] == slot
        and value["sheet_id"] == "sheet-1"
        and value["width_m"] == 11 * 0.0254
        and value["height_m"] == 8.5 * 0.0254
        and value["views"] == value["model_refs"] == []
        and value["sheet_name"].startswith("PrivateSheet")
        and len(value["sheet_name"]) == 28,
        "private blank intent lies outside the frozen source profile",
    )
    for name in ("scale_ratio", "edit_scale_ratio"):
        terms = value[name]
        require(
            type(terms) is list
            and len(terms) == 2
            and all(type(term) is int and 2 <= term <= 47 for term in terms)
            and gcd(*terms) == 1,
            "private source ratio lies outside the frozen domain",
        )
    require(
        (value["scale_ratio"][0] > value["scale_ratio"][1]) == (slot == "Slot02")
        and (value["edit_scale_ratio"][0] > value["edit_scale_ratio"][1])
        != (slot == "Slot02"),
        "private scale edit must change the physical ratio",
    )
    return value
