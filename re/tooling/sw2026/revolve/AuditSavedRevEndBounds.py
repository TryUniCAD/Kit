from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from ProveMeasuredPrincipalRevolve import WriterAudit
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

DISCOVERY = "7e66835b22018dfe16413baf164b6197524ce3191cafe37990d64afc40b82083"
RECOVERY = "401a7b2e5cddacd96deafecc640e9da8967fe979822524fe1abacf149ac42c54"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CASES = ("EndMidplane", "EndTwo", "EndTwoReverse")
PROBLEM = "unsupported SOLIDWORKS body class moLinkedAtomIdNode_c schema 1"


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, pin):
    assert path.is_file() and not path.is_symlink(), path.name
    data = path.read_bytes()
    assert digest(data) == pin, path.name
    return data


def read_lock(path, pin, passed):
    lock = loads(checked(path / "SourceLock.json", pin))
    assert lock["split"] == "discovery" and lock["passed"] is passed and lock["writer_output_count"] == 0
    assert lock["oracle_sha256"] == ORACLE and lock["inputs_unchanged"] and lock["tools_unchanged"]
    assert all(lock[f"control-{side}"]["passed"] for side in ("before", "after"))
    return {source["name"]: source for source in lock["sources"]}


def subject(receipt, name, phase):
    state = receipt["reopened"]
    assert receipt["job"]["case"]["name"] == name and receipt["job"]["phase"] == phase
    assert receipt["passed"] and not receipt["dialogs"] and receipt["source_immutable"]
    assert receipt["oracle_identity"]["file_version"] == "34.5.2.0604"
    assert receipt["oracle_identity"]["sha256"] == ORACLE
    assert receipt["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
    return {"angles_radians": state["angles_radians"], "api_mode": state["api_mode"],
            "reverse": state["reverse"], "bodies": state["bodies"]}


def worker(job):
    raw = b64decode(job["source_bytes"], validate=True)
    assert digest(raw) == job["source_sha256"]
    lookup("utf-16-le")
    audit = WriterAudit(Path("/__KitReadProbeNoOutput"))
    archive = audit.run(lambda: SldprtArchive.from_bytes(raw))
    config = audit.run(lambda: ReadPartConfig(archive))
    assert config.MapValue.CounterValue > 1
    try:
        audit.run(lambda: ReadNativeLink(archive, 0))
    except BodyUnsupported as error:
        assert str(error) == PROBLEM, str(error)
        cursor = error.__traceback__
        frames = []
        while cursor is not None:
            frames.append(cursor.tb_frame.f_code.co_name)
            cursor = cursor.tb_next
        assert "ReadCmgrMut" in frames and "ReadResolvedMut" not in frames, frames
    else:
        raise AssertionError("revisit saved revolve scope because the linked archive has gained support")
    return {"source_sha256": job["source_sha256"],
            "config_map_terminal": config.MapValue.CounterValue,
            "first_refusal": PROBLEM, "blocked_stage": "Contents/CMgr", "audit": audit.report()}


def audit_sources(base):
    first = base / "RevolveEndDiscovery01" / "Capture"
    later = base / "RevolveEndDiscoveryRecovery01" / "Capture"
    authored = read_lock(first, DISCOVERY, False)
    corrected = read_lock(later, RECOVERY, True)
    results = []
    for name in CASES:
        initial = authored[name]
        locked = corrected[name] if name == "EndMidplane" else initial
        root = (later if name == "EndMidplane" else first) / name
        assert locked["passed"] and locked["native_sha256"] == initial["native_sha256"]
        _, original_receipt, edited_receipt = locked["phase_record_sha256"]
        original = loads(checked(root / f"{name}.reopen.json", original_receipt))
        derivative = loads(checked(root / f"{name}-edited.edited-reopen.json", edited_receipt))
        selections = (
            ("original", first / name / f"{name}.SLDPRT", locked["native_sha256"],
             original, original_receipt, "reopen"),
            ("edited", root / f"{name}-edited.SLDPRT", original["edited_derivative"]["sha256"],
             derivative, edited_receipt, "edited-reopen"),
        )
        for role, source, pin, receipt, receipt_sha, phase in selections:
            raw = checked(source, pin)
            result = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                         input=dumps({"source_bytes": b64encode(raw).decode(), "source_sha256": pin}),
                         capture_output=True, text=True, check=False, timeout=30)
            assert result.returncode == 0 and not result.stderr, result.stdout + result.stderr
            results.append({"case": name, "role": role, "native_reopen_sha256": receipt_sha,
                            "native_scope": subject(receipt, name, phase), **loads(result.stdout)})
    return {"schema": "kit.sw2026.saved-revolve-end-delivery-boundary.v1",
            "source_lock_sha256": [DISCOVERY, RECOVERY], "oracle_sha256": ORACLE,
            "fresh_readers": len(results), "results": results, "native_launches": 0,
            "new_heldout_credits": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Distinguish the three cold end modes from earlier independently authored native saves")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--disclosures", type=Path)
    mode.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    print(dumps(worker(loads(sys.stdin.read())) if args.worker else audit_sources(args.disclosures), sort_keys=True))
