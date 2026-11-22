from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import check_model, model_state, read_part, refuse_output, refuse_write
from convert import convert
from convert.adapters.solidworks.Container.Archive import EncodeClass
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

MANAGER = "Contents/CusProps"
INVALID_OWNER_CAUSE = (
    "SOLIDWORKS body moCusPropMgr_c field f20 at 56: "
    "SOLIDWORKS body moCusPropMgr_c field f20/o at 56: "
    "part property manager has unsupported owner placement"
)
ADVANCED_CAUSE = "part properties require an empty compatible native manager"


def is_property_xml(name):
    return name in ("docProps/core.xml", "docProps/custom.xml") or name.startswith("docProps/Config-")


def inspect(path, case):
    raw = path.read_bytes()
    baseline = read_part(raw)
    streams = SldprtArchive.from_bytes(raw).streams
    original_manager = streams[MANAGER]
    cause = None
    if case == "malformed":
        tag = EncodeClass("moCusPropContainer_c", 1)
        if original_manager.count(tag) != 1:
            raise ValueError("missing native keyed property owner")
        streams[MANAGER] = original_manager.replace(tag, EncodeClass("moCusPropMgr_c", 1))
        cause = INVALID_OWNER_CAUSE
    else:
        streams = {name: data for name, data in streams.items() if not is_property_xml(name)}
        if case == "advanced":
            cause = ADVANCED_CAUSE
    changed = BuildSldprt(streams, Template=raw)
    copied = SldprtArchive.from_bytes(changed).streams
    if copied[MANAGER] != streams[MANAGER] or (
        case != "malformed" and any(is_property_xml(name) for name in copied)
    ):
        raise ValueError("binary manager variant disagrees with its scoped input")
    observed = read_part(changed)
    check_model(baseline, observed)
    operation = partial(
        convert, changed, source_format="solidworks.sldprt",
        destination_format="interchange.json", include_tessellation=False,
    )
    state = model_state(observed)
    if cause is None:
        state["portability_refusal"] = refuse_output(
            operation, "native-only feature definitions cannot be exported",
            "sldprt:feature:-1", "Sheet-Metal Master",
        )
    else:
        state["refusal"] = refuse_write(operation, cause)
    if path.read_bytes() != raw:
        raise ValueError("binary source changed")
    state["source_sha256"] = sha256(raw).hexdigest()
    state["manager_sha256"] = sha256(original_manager).hexdigest()
    state["property_xml"] = sorted(name for name in copied if is_property_xml(name))
    state["geometry_equal"] = True
    return state


if __name__ == "__main__":
    cases = ("malformed", "advanced", "empty")
    paths = tuple(map(Path, sys.argv[1:]))
    print(json.dumps({
        name: inspect(path, name) for name, path in zip(cases, paths, strict=True)
    }, sort_keys=True))
