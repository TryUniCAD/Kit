# Fusion writer measurement evidence

The archives in this directory are Kit-generated candidates from the
[integrated encoder run](https://github.com/TryUniCAD/Kit/blob/93e87aa51fa0bd470c97eb587f1565cf44ce45e0/re/Fusion/EncoderRoundTrip/NativeEvidence.md#integrated-cli-reconstruction-and-edit).
The original Fusion 2706.1.17 process measurements used independently
authored controls at the requested candidate dimensions. Each case
contains one constrained origin-based cuboid with a 16.4 by 27.1 mm
rectangle. Each candidate opened and rebuilt, then was edited to 28.3 mm,
restored, saved and reopened in a separate process.

| Candidate | Initial height (mm) | Initial volume (mm³) | Candidate SHA-256 | Receipt SHA-256 |
| --- | ---: | ---: | --- | --- |
| [Reconstruction](reconstruction.f3d) | 13.8 | 6133.272 | `bb662739916ed12c21680f9e4b53f553625ea799f066ba4e7d2f88417ea55112` | `5f2d54b0efe634bde01930c98ae6494fba5db3c467fc37059cfbca5df8727356` |
| [Edited](edited.f3d) | 22.6 | 10044.344 | `8865a3153326e52034c9110ccfe5c14ec857d2bde524a723c8144bd8907abc8a` | `8e69751b17e255350f74fb92c47dcc294c3b33fb854f991c9f91044c26345106` |

The [reconstruction](reconstruction-receipt.json) and [edited](edited-receipt.json)
receipts retain measurements and full raw stage SHA-256 references. The
four [reconstruction stages](Reconstruction/) and four [edited stages](Edited/)
match those references. They apply to these bytes. Fusion-saved
auxiliary-bearing variants need separate reader and writer qualification.
