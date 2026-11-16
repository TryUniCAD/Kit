# Curve discovery source fixture preparation

`PrepareCurveCorpus.py` prepares 24 locked discovery parts and two original controls for remote archive research.
It leaves the legacy ladder and assembly preparer unchanged.
The six held-out native files remain outside its selection.

## Inputs and use

Use Python 3.11 or later in a fresh interpreter.
Supply the complete original source root, a new destination, both expected evidence hashes, and each private account name.
Use canonical paths without symlinks and an existing destination parent.

For the inspected `CurvesSourceLock02` source, the lock hash is
`21da3f3e8a6e2a6fe732f69c377a9539bc26a3ee1111795319b4a95d0124ad25`.
The original root-verification hash is
`0b9e314b871ec27ef1e0e21a60504d5cc107de632127f33267ce53c68d301403`.

The following example describes the interface; it has not been executed for this change:

```sh
uv run --no-sync --python 3.11 python re/tooling/sw2026/PrepareCurveCorpus.py \
  /private/OracleSource/CurvesSourceLock02 /private/PreparedCurveDiscovery \
  --expected-lock-sha256 21da3f3e8a6e2a6fe732f69c377a9539bc26a3ee1111795319b4a95d0124ad25 \
  --expected-proof-sha256 0b9e314b871ec27ef1e0e21a60504d5cc107de632127f33267ce53c68d301403 \
  --redact-name PRIVATE_ACCOUNT_NAME
```

The tool checks each selected original part and manifest against their frozen lock hashes.
It also checks source pass results, build identity, tool hashes and unchanged-source verification.
It reads lock hash metadata but never selects or traverses held-out native paths.

## Privacy transformation

The tool preserves every valid native stream, its name and its order.
It replaces recognized short Unicode CString metadata and supported XML metadata text at equal encoded width.
Unknown private contexts cause failure before destination creation.
This checks string framing; it does not parse complete parametric archive fields.

Qualified CAD dimensions contain `@` separators and can resemble email substrings.
The discovery metadata review found 285 such email-pattern matches in technical dimension observations.
Exact technical identities come only from frozen `FullName` API results and dimension records.
Each identity must have a dimension prefix, nonempty qualified components and a final `.Part` document component.
Email-only exceptions require a whole structured JSON string, short Unicode CString, or supported XML text frame.
Account names and home paths still take precedence.
Other API results and arbitrary email strings receive no exception.
The home-path rule explicitly recognizes both `\\Mac\Home\` and `//Mac/Home/` prefixes.

The bounded loader executes real repository container modules and their explicit metadata dependencies.
It skips SDK package initializers and records every executed repository module hash.
It supplies no mocked class, container behavior or vendor software.
It loads no archive schemas and performs no conversion or writer synthesis.

The output contains 26 flat `.SLDPRT` files and three JSON records:

| Record | Content |
| --- | --- |
| `Manifest.json` | Exact membership, original/prepared hashes, source specifications, observed source results and all stream hashes |
| `PrivacyLedger.json` | Replacement contexts, encoded widths and hashes of original/replacement text |
| `SourceEvidence.json` | Final manifest/ledger hashes, original lock/proof identity, source verification and module provenance |

Original private strings are represented by hashes in the ledger.
The ledger also lists the exact source dimension identities used by the framed email rule.
Source evidence integers, including FILETIMEs, remain exact Python integers.
The original native files and manifests remain unchanged.

## Limits and failures

Prepared fixtures are discovery/control parser inputs, not Kit-generated parts or held-out writer evidence.
Original native acceptance does not transfer to the modified copies.
The container is rebuilt without claiming whole-file byte identity or native acceptance.
Full model, archive-schema, linked-map and round-trip verification runs in remote CI.
The companion process fixture requires 208 critical/header stream checks and 26 linked resolved-stream checks.
It checks the exact fixture membership and hashes against the portable source lock.
Used provisional schemas, missing schemas, unread tails and byte differences fail those checks.
These are expected checks, not execution results recorded by this change.

The privacy scan covers supplied account names, home paths and email patterns in supported text encodings.
It does not establish exhaustive privacy review of images or unknown embedded encodings.
Review those assets before repository publication.
If writing fails, a partial destination can remain; select a fresh destination after inspecting that failure.
Existing output is never overwritten.

## Actual verification

The private implementation received source inspection and AST/format checks only.
The preparer, container modules, archive schemas and tests were not executed by the implementation worker.
No source files were transformed and no prepared corpus was created during that work.

The owner subsequently ran the committed preparer at
`f9fd31d3f9bc82b6ab65c4b1cdb580b8be9e9a56` for actual research data preparation.
The [preparation record](../../../../re/solidworks/measurements/2026/CurveDiscoveryPreparation.json)
binds 26 prepared native files totaling 1,571,839 bytes, 1,040 stream records,
286 framed stream redactions and 26 structured-metadata redactions.
The ledger retains 77 exact qualified dimension identities.
The [prepared corpus](../../../../re/solidworks/v2026/corpus/curves-discovery/Manifest.json)
has manifest SHA-256 `83fdec0c415f6b2152d8df6bb12deba1b24313e8580597452505b139ec59a42e`.
All prepared-file hashes were checked against that manifest without executing archive schemas.

An independent visual reviewer inspected all 26 extracted native `PreviewPNG` images individually.
The [hash-bound review](../../../../re/solidworks/measurements/2026/CurveDiscoveryPreviewReview.json)
records gray geometry on white backgrounds and no visible private text or application UI.
This is a nonexhaustive visual privacy review, not native CAD acceptance.
Only the 16 bounded container/metadata dependency modules executed during preparation;
archive-schema, round-trip, product-verification and test execution remain in remote CI.
The process fixture requests 208 strict critical/header comparisons and 26 linked resolved comparisons.
Their results remain pending.

The preceding independent anatomy study inspected only D01 and D19 discovery inputs.
Both contained 40 valid compressed streams.
Private metadata appeared in seven streams, including load-critical binary streams.
The identified wide metadata strings had short Unicode CString framing.
These two observations do not establish full-family grammar or privacy completeness.

See the [framed-redaction gotcha](../../../Gotchas/Conversion/Solidworks/Archive/BinaryMetadataNeedsFramedRedaction.md),
[research serializer guide](../../../../re/tooling/sw2026/serial/README.md),
[research artifact policy](../../../Reference/Research/ResearchArtifacts.md),
and [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md).
The criteria state: “The first is success under every criterion on this page.”
They also state: “The second is the end of the available context.”
This fixture-preparation addition does not close the unfinished native-writer goal.
