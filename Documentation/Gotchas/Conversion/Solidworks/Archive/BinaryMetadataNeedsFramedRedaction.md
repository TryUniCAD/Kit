# Binary fixture metadata needs framed redaction

## Expectation

Removing account names from document XML removes personal metadata from a native part fixture.
A printable-byte regex is sufficient to identify safe binary string boundaries.

## Observed behavior

The independent D01 and D19 curve-discovery anatomy study found private text in seven native streams.
These included `Header2`, `Contents/Definition`, `Contents/DisplayLists`, the model header, biography, and two property XML streams.
Each inspected file contained 40 valid compressed streams.

The wide private strings had explicit short Unicode CString framing.
They were not isolated by container decompression alone.
The existing ladder preparer's `redact()` scans printable bytes; that operation does not establish typed field ownership.

The discovery JSON metadata also contains qualified CAD dimension identities.
For example, `D1@CurveBoss@D01CircleRadius.Part` resembles an email address when matching begins after its first separator.
The broad email pattern matched 171 `FullName` results, 57 author dimension names and 57 verify-job dimension names.
These 285 discovery occurrences were technical identifiers.
No other email-match contexts appeared in that metadata review.
This observation does not justify exempting arbitrary email addresses or API results.

The original D01 SHA-256 is `e6615329888108657debef922af95c8d7f6c417bd131e23da2baff0b48ac73aa`.
The original D19 SHA-256 is `f2d1bafc081e1576bf3542076ae2d346bdc792c8585b2d20121fb09e68965294`.
These are discovery inputs, not held-out files or generated writer outputs.

## Workaround

Recognize the CString frame or XML metadata context before replacing text.
Preserve encoded payload width and string framing.
Reject a private occurrence outside the supported metadata contexts.
Record source/prepared hashes and hash the original private replacement content.
Preserve the original source evidence outside the checkout.

Derive exact dimension identities only from frozen `FullName` API observations and dimension records.
Validate the dimension prefix, qualified components and final `.Part` document component.
Preserve these identities only when the whole value has a recognized JSON, CString or XML text frame.
Keep account/home detection active inside those frames.
Unframed matches and actual emails retain the ordinary privacy checks.
Recognize both backslash and forward-slash Mac-home prefixes.

`PrepareCurveCorpus.py` applies this bounded transformation to the locked discovery/control selection.
Its ledger proves which bytes changed; it does not establish full parametric grammar.
Remote CI must parse and re-emit the resulting archive streams through their real schemas.
Prepared files need separate native measurements before any native-acceptance claim.
Review previews and unsupported embedded encodings before publication.

See the [preparation change](../../../../Changes/Solidworks/Model/SolidworksCurveDiscoveryCorpus.md),
[research preparer](../../../../../re/tooling/sw2026/PrepareCurveCorpus.py),
and [CAD success criteria](../../../../Reference/Operations/CadSuccessCriteria.md).
