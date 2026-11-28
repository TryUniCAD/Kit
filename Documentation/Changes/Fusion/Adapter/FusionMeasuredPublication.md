# Fusion publication with exact offline measurements

The Fusion writer reports vendor loadability and application usability only when
an offline receipt matches the complete F3D archive it generates. A strict SDK
write or a CLI conversion to F3D requires that receipt. A default SDK write can
still prepare a native candidate. Its result reports both acceptance flags as false.

1. Write a candidate with the default SDK policy.
2. Measure it in Fusion with the [cuboid oracle](../../../../re/Fusion/LocalOracle/EncoderRoundTrip/README.md).
3. Open the original candidate with strict `open_document`. Supply the parsed
   receipt in `values={"fusion_native_measurement": Receipt}` to
   `write_document(..., allow_carrier=False)`. For the CLI, pass
   `kit convert Candidate.f3d Output.f3d --native-measurement Receipt.json`.

The supported receipt covers one constrained, untapered cuboid. Kit checks
the candidate SHA-256, equivalent independent controls, distinct processes,
body count, feature inventory, bounds, volume and centre of mass. It checks
the named height driver, rebuild, restoration and fresh reopen of both saves.
It calculates expected initial and edited geometry from the validated
candidate specification. Position comparisons use an absolute tolerance of
0.0000001 mm. Volume uses 0.00001 mm³. Both use a relative tolerance of 0.00000001.

The caller determines whether to trust the unsigned offline receipt. Kit
checks the receipt and its binding to the generated data without launching
Fusion. Use an empty, seekable binary stream at position zero for SDK stream
output. Missing or mismatched evidence refuses strict publication before
the destination changes. Independent authoring can generate new data on each
invocation. Measure the saved candidate and re-emit its strict readback.

The [retained measurements](../../../../re/Fusion/WriterMeasurement/README.md)
document two candidates previously measured in Fusion 2706.1.17. The shared
integration cases cover the SDK and CLI, absent and incorrect evidence,
wrong driving edits, reused process identity and nonempty destination streams.
The focused Windows run with Python 3.14.6 passed all 32 affected integration
and compatibility cases. The donor replay scan and scoped Python steering passed.
