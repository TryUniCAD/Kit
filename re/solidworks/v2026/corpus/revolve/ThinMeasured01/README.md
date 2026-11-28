# Disclosed thin-revolve suite evidence

`DisclosedEvidence.json.gz` contains six exact UTF-8 JSON texts. The two
model specs are independently authored neutral instructions for the
disclosed Front, Top and Right cases. Each is paired with its original
inspection job and the associated SOLIDWORKS 2026 SP05.2
(`34.5.2.0604`) native terminal receipt. The bundle contains only
disclosed models and audit metadata. It has SHA-256
`f72de5faf4bc7f849dd0bc48443312700b06641d6cd06aa817f8249bac06edba`.
Each individual decompressed text has its own prior SHA-256 pin.

The Front texts come from `SdkThinGenerated01`; the principal text
group comes from `SdkThinPlaneGenerated01`. Its terminal receipt is
preserved at `5664d5533:re/solidworks/measurements/2026/SdkThinRevolvePrincipalNative01.json`.
These are Kit interoperability records. The jobs retain the links to
their original model specs and observations.

The complete-suite worker uses the unequal two-wall Front case and the
Right midplane case. It generates the complete archives from the model
in each worker. Payloads from the native files are unnecessary because
the authenticated report already identifies each complete candidate SHA-256.
[Procedure and scope](../../../../records/MeasuredThinRevolve2026.md)
