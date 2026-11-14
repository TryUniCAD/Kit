# CATIA measurements

## Corpus

| Item | Value |
| --- | --- |
| Parts | 27 |
| Products | 3 |
| Parts with decoded native B-rep | 25 |
| Parts with unsupported layout | 2 (`4876.CATPart`, `4876_1.CATPart`) |
| Products with decoded names and references | 3 |
| Products with decoded transforms | 0 |

## Reader checks

`re/catia/tooling/ParseBrep.py` decodes 25 of 27 parts. `re/catia/tooling/BuildModel.py` validates
every decoded model with zero errors.

## Writer check

A six-face box emitted by `NativeWriter.BuildPart` reads back as six faces, twelve edges, and eight
vertices with zero validation errors.

## Vendor acceptance

Not measured. The Parallels Windows 11 VM has CATIA V5-6R2022 installed at
`C:\Program Files\Dassault Systemes\B32\win_b64`, but the CATIA COM class returns
`CREATE_ERROR=429` and `CNEXT.exe` exits without a license. `DSCheckLS.exe` reports that
`C:\ProgramData\DassaultSystemes\Licenses\DSLicSrv.txt` is unavailable. No license file or license
server is configured.

The acceptance procedure in `Documentation/Reference/Operations/CadSuccessCriteria.md` therefore
remains open. The writer reports `vendor_loadable=False` and `application_usable=False`.

## Next oracle step

1. Configure a CATIA license in the VM.
2. Open a known control part and record body count, volume, and center of mass.
3. Open the emitted box and record the same values.
4. Rebuild and record errors.
5. Change a driving dimension and rebuild.
6. Measure the control again.
