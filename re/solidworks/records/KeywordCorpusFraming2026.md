# SOLIDWORKS 2026 KeyWords framing across the tracked corpus

Task `B03-SW2026-ARCHIVE`, PR #121. This comparison extends the exact-build
KeyWords and container-version re-verification across the checked-in
2026 part and assembly evidence. Its input set comes from Git revision
`5554733fde548afabdc6db221f387163d15e9497` and includes all 80 parts and
eight assemblies under `re/solidworks/v2026/`. It reads pinned Git blobs
and leaves the native files untouched.
[Earlier exact-build comparison](Solidworks2026ArchiveCompatibility.md)

Both independent host runs produce the same receipt. All 88 containers
report version 4 and model archive 19000. All 88 KeyWords streams begin
with `0x86`, the quoted UTF-8 XML declaration and CRLF. Their closing
element is followed by CRLF, giving two pairs and zero bare LF bytes. The
ordinary XML parser consumes all 88 streams. Reassembling each decoded XML
tree with compact empty tags reproduces exactly 88 of 88 streams. The
spaced form matches zero input streams.

The XML contains 2,070 `Feature`, 173 `Sketch`, 85 `Extrusion`, 183
`Dimension` and nine `Reference` elements. All six `DissectableChildren`
fields in the cohort carry one decimal ID. The linked field authority,
multi-child form and all feature-specific generation remain separate from
this lexical comparison. The audit reads no sealed inputs and runs no
native processes or writers.
[Emitter and field limits](MetadataConstruction2026.md#keywords-framing-and-evidence-limits)

```sh
python3.14 -B re/tooling/sw2026/AuditKeywordCorpus.py \
  5554733fde548afabdc6db221f387163d15e9497 /tmp/UnusedKeywordCorpus.json
```

The [numeric receipt](../measurements/2026/KeywordCorpusFraming01.json) has
SHA-256 `3d364bb0779efc1076d4c1d89a472e0aac5835a628a0ca505cc6ea80e0cd1ce4`.
It binds the exact tool and four codec sources, a per-file container and
stream fingerprint and the element inventory.
