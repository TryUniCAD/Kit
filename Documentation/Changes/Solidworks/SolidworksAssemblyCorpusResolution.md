# Assembly corpus resolution

## Behavior

Real SOLIDWORKS assemblies reference component parts by Windows source paths. Those
paths are normally NFC, while macOS often stores the adjacent files with decomposed NFD
names. The assembly reader now normalizes both the component index and each lookup to NFC
before casefolding, so an accented component such as `ADMISIÓN.SLDPRT` resolves regardless
of which Unicode form the file system reports.

A corpus-gated integration case, `TestASMHead`, opens the tracked
`Cylinder Head Assy 1.SLDASM` through the public reader, requires zero
`sldasm.component_source_missing` diagnostics, writes it with `allow_carrier=False`, and
requires a self-contained, application-usable, near-lossless result whose bundled
component count, instance count, mate count, and re-read assembly match the source.

## Usage

No option is required. `open_document` resolves adjacent components automatically when
the document has a file path. A caller that reads from bytes can pass
`component_search_root` in the read options to point at the directory holding the parts.

## Limitations

- the normalization fixes name comparison only; a genuinely missing component still
  reports `sldasm.component_source_missing` and still fails a `allow_carrier=False` write
  with `external_requirements`
- from-scratch mate generation remains unimplemented; the tracked assemblies above carry
  their saved mate streams through the template path
- `SLDDRW` remains unsupported and is rejected at
  `src/convert/adapters/solidworks/container/Format.py:208`

## Verification

`tests/convert/solidworks/assembly/SolidworksAssemblyEnvelopeTests.py` contains:

- `TestASMUnicode`, which opens the tracked `ENSAMBLE 3_IZQUIERDO.SLDASM`, requires
  resolved component documents and no missing-source diagnostic, then requires a
  self-contained, application-usable, near-lossless write.
- `TestASMHead`, which does the same for the tracked `Cylinder Head Assy 1.SLDASM`
  (11 component documents, 119 instances, 240 mates), requires 12 output files, and
  requires the re-read assembly to equal the source.

Both run in CI against tracked files, so no local corpus or SOLIDWORKS install is needed.
The NFC/NFD failure and the audit evidence for the larger 63-file example directory are
recorded in [Unicode component names](../Gotchas/Conversion/SolidworksUnicodeComponentNames.md).
