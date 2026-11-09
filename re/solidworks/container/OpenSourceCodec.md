# Native stream codec repair

## Source audit

The implementation adapts the MIT-licensed openswx rotation codec at
`72291dc962bbf267fa40cd57813b273108ebac53`, and follows its payload-boundary
advancement and cache-cell recognition. Full attribution is shipped in
`src/convert/adapters/solidworks/container/OpenSwxLicense.md` and wheel license metadata.

The modern parser uses the file header's final byte as the name rotation key.
Version 4 is the familiar nibble swap; version 3 requires rotate-left by three
on read and rotate-right by three on write. Both local and central directory
names must use the selected version. A template-based rewrite now defaults to
the template version, while an explicit version still requests conversion.

Kit previously scanned inside accepted compressed payloads, allowing a complete
encoded record embedded in a stored DEFLATE block to become a sibling stream.
The scanner now advances to each accepted payload's end. It retains fail-closed
handling of genuinely ambiguous duplicate physical streams; neither upstream
nor this repair establishes authoritative active-directory selection for all
native container variants. In particular, the repository's real sample has
cache records and trailing container state, so treating every document as a
conventional ZIP with a terminal EOCD would be incorrect.

Cache cells have CRC-slot = twice logical size modulo 2^32, compressed-size-slot
= half logical size, and nonzero logical size. These are classified before
inflation. Recognized data records now reject truncated payloads, bad CRCs,
wrong decoded sizes, unfinished DEFLATE frames and trailing compressed bytes.
Inflation is bounded to advertised size plus one, with an aggregate decoded
size budget across accepted records.

## Candidates and limits

- openswx: MIT at the pinned commit above; native reader, no native writer.
- sldkit: legacy MIT commit `c43b5ef752a0e58535b7f8f744f7d7c68e3c0e90`;
  current new material at `6e50664343351e7c2c77844f2b839ddc5a8964b1` is
  PolyForm Noncommercial. It is not adopted as a runtime dependency.
- cadmpeg: Apache-2.0 code at `007eb640985bf34b8042591030c9891df5f8945f`;
  describes its SLDPRT support as L1 with partial semantic writing. Its directory
  and cache handling does not establish full native feature-history writing.

No examined candidate supplies a complete, vendor-verified, editable native
SOLIDWORKS writer. This change repairs the container codec, not every unsupported
feature family, drawing semantics, legacy OLE2 support, or unresolved geometry.
It does not claim vendor loadability or editable rebuild acceptance for new
feature families.

## Verification route

`NativeCodecTests.py` exercises the actual adapter and retained-source writer
using a real model's streams wrapped by an independent Python zipfile-based
fixture encoder. It covers versions 3 and 4, wire name encoding, version
preservation and override, embedded misleading records and damaged input.
The focused compatibility workflow runs this and the existing native adapter
checks on the PR. No tests are run locally. Full acceptance and the target
application oracle remain separate from the codec integration results.
