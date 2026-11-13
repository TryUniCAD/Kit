from __future__ import annotations
import hashlib
from pathlib import Path as PathInfo
from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.configuration.ConfigZero import encode_config0_stream

Source = PathInfo(".rescratch/polyline/kit-five-new-cmgr.SLDPRT")
Control = PathInfo(".rescratch/polyline/poly5a.SLDPRT")
Target = PathInfo(".rescratch/polyline/kit-five-composed2026-v2.SLDPRT")
Archive = SldprtArchive.open(Source)
Payload = encode_config0_stream(PartName="Part1", Generation=19000)
Healthy = SldprtArchive.open(Control).require("Contents/Config-0")
Deltas = [
    (Index, Left, Right)
    for Index, (Left, Right) in enumerate(zip(Payload, Healthy, strict=False))
    if Left != Right
]
print("bytes", len(Payload), "matches_reference", Payload == Healthy, "different_bytes", len(Deltas), "first", Deltas[:32])
print("sha256", hashlib.sha256(Payload).hexdigest())
for Label, Offset in (
    ("transref", 2796),
    ("sf-one", 16483),
    ("sf-two", 17612),
    ("sf-three", 17934),
    ("swift", 19730),
):
    print(Label, "present", Payload[Offset:Offset+16].hex(), "expected", Healthy[Offset:Offset+16].hex(), "matches", Payload[Offset:Offset+16] == Healthy[Offset:Offset+16])
Streams = dict(Archive.streams)
Streams["Contents/Config-0"] = Payload
Target.write_bytes(BuildSldprt(Streams, Template=Source.read_bytes()))
print(Target)
