from __future__ import annotations

from Core import Obj
from builders.Metadata import integer


def target_update_stamps(model: Obj) -> tuple[int, int]:
    if not isinstance(model, Obj) or model.cls not in ("moPart_c", "moAssembly_c"):
        raise ValueError("reference stamp derivation requires an ordinary generated model")
    geometry = integer(model["f1300"], "model geometry stamp")
    transform = 101
    if model.cls == "moPart_c":
        return geometry, transform
    references = tuple(row["o"] for row in model["f68"]["list"]["items"]) if model["has_list68"] else ()
    if len(references) != model["f1560"]:
        raise ValueError("assembly stamp derivation requires the complete direct occurrence graph")
    for reference in references:
        if not isinstance(reference, Obj) or reference.cls != "moReference_c" or reference.get("owner") is not model:
            raise ValueError("assembly stamp derivation requires its owned ordinary occurrences")
        geometry = (geometry + integer(reference["f3f4"], "target geometry stamp")) & 0xFFFFFFFF
        incoming = integer(reference["f3f0"], "local transform stamp")
        transform = incoming if transform == 101 else (transform + incoming) & 0xFFFFFFFF
    return geometry, transform
