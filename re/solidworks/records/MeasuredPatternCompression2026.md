# Native comparison for the alternate pattern compressor

The measured pattern archives reproduced under classic zlib 1.2.12.
An SDK runtime using zlib-ng can compile different complete file bytes
from the same neutral input. Equal uncompressed streams support a
compression comparison. Publication still requires a receipt for the
complete archive. This procedure stages a disclosed research batch only.

## Freeze and capture

Freeze the committed checkout's `src/` with `git archive`. The root
`.gitattributes` omits `re/` from Git archives. Append the committed
`re/tooling/sw2026/CheckMeasuredPattern.py` blob and the five JSON members
under `re/solidworks/v2026/corpus/linear-pattern/MeasuredCold01/` to the
same archive using their exact `git show <commit>:<path>` bytes. Extract
the result into a fresh directory and reproduce a classic capture to
verify both the SDK source fingerprint and worker SHA. Record the commit,
SDK tree ID and archive SHA-256. Use that unchanged snapshot with the
hash-pinned guest Python distribution.

Run the two classic witnesses in fresh Python 3.14 processes. Use a new
working directory with an empty `Classic` parent.

```sh
python3.14 -I -B re/tooling/sw2026/CheckMeasuredPattern.py \
  --case ColdRaisedPatternA --capture-candidate Classic/ColdRaisedPatternA
python3.14 -I -B re/tooling/sw2026/CheckMeasuredPattern.py \
  --case ColdRaisedPatternB --capture-candidate Classic/ColdRaisedPatternB
```

The guest owner uses the same frozen code with the pinned Windows Python
that reports zlib-ng. In a fresh Windows working directory, set
`$EmbeddedPython` to that exact interpreter and `$Source` to the
extracted, hash-verified source bundle.

```powershell
$Worker = Join-Path $Source 're\tooling\sw2026\CheckMeasuredPattern.py'
foreach ($Series in @('Alternate', 'Repeat')) {
    New-Item -ItemType Directory -Path $Series | Out-Null
    foreach ($Case in @('ColdRaisedPatternA', 'ColdRaisedPatternB')) {
        & $EmbeddedPython -I -B $Worker --root $Source --case $Case `
            --capture-candidate (Join-Path $Series $Case)
        if ($LASTEXITCODE -ne 0) { throw "capture failed for $Series/$Case" }
    }
}
```

Each role folder contains an exclusively created raw candidate and
`Capture.json`. The alternate branch captures only after both public
writer routes refused the new digest without writing, and strict
native-history and analytic geometry checks passed. Capture bookkeeping
outside the guard fingerprints the worker and SDK sources. The
measurement inside the guard must record zero reads and native launches.

## Compare and stage

On the host, pass the original disclosed packet from
`GeneratedLocalPatternNative02/Packet`, the three capture roots, and a
new `Packet` directory. Preserve the old packet and native result.

```sh
python3.14 -I -B re/tooling/sw2026/StagePatternCompression.py \
  "$OriginalPacket" --classic Classic --alternate Alternate --repeat Repeat \
  --output "$NewBatch/Packet"
```

`--verify-original` verifies the original packet, its 28 control,
tool and metadata members, and the two independent model/locator
contracts without creating output. The complete stage additionally
requires exact classic measured digests, identical SDK source fingerprints,
two fresh Windows zlib-ng captures per role, exact repeat file bytes,
identical format ID, version, record order and all ten uncompressed
stream hashes, and at least one altered compressed stream per file.
Any disagreement stops staging. `Compression.json` links capture
digests, the clear streams and changed compression records. The new
build manifest provides the actual alternate candidate digest and
length with the existing independently authored model predictions.
The stage reads the disclosed control and tools only after verifying
their original hashes. It uses neither old candidate file as input.

## Native measurement

The guest owner brings the new packet into a fresh isolated batch and
verifies the emitted `packet_sha256` before launch. The existing
observer requires the exact encoded locators under
`C:\KitGeneratedLocalPattern` and a fresh directory lease there.
Preserve any older lease and its receipts before reserving the
same logical locators. A different locator needs its own generated
candidate and measurement.

Use the already qualified current-user Python with the installed native
interop available. The guest owner invokes the hash-pinned observer
through the established Parallels transport.

```powershell
& $CurrentUserPython -E -B "$Packet\Tools\ObserveGeneratedLinearPattern.py" `
    $Packet --pin $PacketSha
```

Require the exact app build `34.5.2.0604` and executable SHA
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
Require the original control before and after, six distinct process
lifetimes, the two immutable alternate candidate digests, clean
open/rebuild, the exact linked tree, body count, face count, volume,
area, centre of mass and bounds, native driving D1/D3, the actual pitch
edit and save, and a fresh read-only reopen of each edited result.
The frozen observer checks those values against the same independent
plan and refuses any failed control or candidate. Check the resulting
packet and build SHA bindings and preserve the raw native record and
transport exit evidence before considering a positive publication test.

Host preflight verified the old custody and checked guarded classic
captures. Actual alternate captures and native acceptance of those
digests remain pending. Neither the staging report nor a previously
measured classic result grants permission to publish an alternate file.
