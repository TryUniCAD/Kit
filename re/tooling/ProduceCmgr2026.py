from __future__ import annotations
from pathlib import Path as PathInfo
import hashlib
import struct
from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.container.Cmgr import encode_cmgr_stream

Source = PathInfo(".rescratch/polyline/kit-five-typed-definition.SLDPRT")
Control = PathInfo(".rescratch/polyline/poly5a.SLDPRT")
Candidate = SldprtArchive.open(Source)
Healthy = SldprtArchive.open(Control)
Payload = encode_cmgr_stream(Generation=19000)
Reference = Healthy.require("Contents/CMgr")
Differences = [
    (Index, Left, Right)
    for Index, (Left, Right) in enumerate(zip(Payload, Reference, strict=False))
    if Left != Right
]
print("stream_bytes", len(Payload), "operations_widths_verified_factory", Payload != b"")
print("source_matches", Payload == Reference, "different_bytes", len(Differences), "first", Differences[:24])
print("sha256", hashlib.sha256(Payload).hexdigest())
for StreamName, Value in (("Contents/Config-0", Healthy.require("Contents/Config-0")),):
    Streams = dict(Candidate.streams)
    Streams[StreamName] = Value
    Target = PathInfo(".rescratch/polyline/kit-five-new-cmgr.SLDPRT")
    Streams["Contents/CMgr"] = Payload
    Target.write_bytes(BuildSldprt(Streams, Template=Source.read_bytes()))
    print(Target)
for Index in range(395, 465, 4):
    print(Index, Payload[278+Index:278+Index+4].hex(), struct.unpack_from("<f", Payload,278+Index)[0])
