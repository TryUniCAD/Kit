from __future__ import annotations

from hashlib import sha256 as HashValue

from interchange.document.models.DocumentModel import CadDocument


def GetFingerprint(Value: CadDocument) -> str:
    Parts = (
        repr(Value.configurations),
        repr(Value.parameters),
        repr(Value.support_planes),
        repr(Value.sketches),
        repr(Value.selections),
        repr(Value.feature_timeline),
        repr(Value.bodies),
        repr(Value.meshes),
        repr(Value.brep_payloads),
        repr(Value.units),
        repr(Value.assembly),
        repr(Value.brep),
        repr(Value.materials),
        repr(
            {
                KeyText: ItemValue
                for KeyText, ItemValue in Value.metadata.items()
                if KeyText not in {"creo.source_bytes", "creo.fingerprint"}
            }
        ),
    )
    return HashValue("\x1f".join(Parts).encode("utf-8")).hexdigest()
