# Native mass variant framing for the oblique-cylinder diagnostic

Task `B04-SW2026-FREECAD-CYLINDER`, owner `assembly_occurrence`, delivery PR #121. This is the narrow second observer packet for the [mass precision diagnostic](ObliqueCylinderMassPrecisionProtocol2026.md). The first packet and all earlier source failures remain immutable and failed. No geometry, analytic target, tolerance, source-author operation or writer changes here. Root alone executes the native oracle.

## Actual first-packet result

The first trial SHA-256 remains `52a51eeaa8a6e60a1da06b0870c45f574f69242391dd3719c28c44e444462d0b`. Both disclosed pristine controls opened/rebuilt with zero errors/warnings, one actual body, healthy history and no cleanup errors. Their full diagnostic verdicts were false: the new document result parser rejected all six successful COM calls. Neither F01 nor F02 ran through this diagnostic.

| Preserved control | Result SHA-256                                                     | Raw record SHA-256                                                 |
| ----------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Before            | `6f442b8328ab68fd0fb72a5f070cf1a3fc3226adf7c898249b6ee82a5b5dbfc0` | `e0cec59851b7404ce0337cdf0659c1c13ce722dc2df2d72d1475dd7a2392ef85` |
| After             | `caee1b42c2bcf2fa9460618efa2f4fc5921ead23b4e9a27e697f8ee20c204a5e` | `da417cdd044a3b61a074fb767129e223e148a894a74d65e7c24b55d214d83c7b` |

Each actual `InvokeTypes` return has two outer values: a thirteen-double metric array and separate integer status zero. Every metric prefix has the ordinary twelve fields; its final extra value is exactly `0.0`, `1.0` or `2.0` for the requested accuracy in both controls. The original parser required twelve fields and recorded `native mass result must contain twelve metrics` in every level row. Those caught per-level failures did not populate the recorder's top-level `first_failure`; the existing false verdict and six errors are preserved rather than recast as COM failures.

The registered signature still returns one VARIANT plus its separate output I4 status. VARIANT does not fix the SAFEARRAY length. pywin32 returns the actual result followed by output arguments; it did not add the thirteenth array field or move status into that array. [pywin32 typed invocation](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/PyIDispatch.cpp)

The published document-method contract describes twelve metrics in SI and the part's default model frame. The observed extra value is retained separately, and its internal semantic role remains unproved beyond equality to the requested accuracy in these six calls. A sibling method's thirteen-field documentation is not silently substituted for this interface. [Published document-method contract](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldocextension~getmassproperties2.html)

## Bounded second-packet grammar

[ObliqueMassShape.py](../../tooling/sw2026/oblique_mass/ObliqueMassShape.py) retains the actual top-level/child types, counts, finite scalar values and a bounded recursive shape before parsing. It never calls arbitrary object representations or iterates an unknown object.

The document-only framing helper accepts the documented twelve-field form, or the observed exact thirteen-field form with all finite numeric fields, a floating final value equal to the requested level and separate integer success status. It rejects other counts, outer shapes, nested fields, nonfinite values, noninteger status and unmatched tails. The original twelve fields go through the unchanged positive-volume/area metric parser. A thirteen-field record also carries its complete original array, explicit extension index/value and `all_extension_semantics_proven=false`. This is an instrument for a controlled measurement, not format-field qualification.

The `IBody2` parser remains strictly twelve fields. Its before/after results matched the original control's volume `8.000000000000001e-6 m³`, area `0.0028 m²` and centroid `(0,0,0.005) m` exactly. The document prefix also matches those geometric values. Its measured mass is about `0.008 kg`, while the body call explicitly uses density `1 kg/m³` and returns about `8e-6 kg`; the separate document context reports density about `1000 kg/m³`. These contexts are retained independently. No full mass parity or units defect is inferred.

Every geometry comparison still uses the original `rel_tol=2e-7`, `abs_tol=1e-12`. The candidate native author phase, control qualification, actual body parser and comparison functions retain identical ASTs. No alternative measurement substitutes for an original default failure. The first new pristine control must still qualify all explicit API calls before either disclosed candidate starts.

## Missing-result summary

`InspectObliqueMass.py summary --no-file` emits a complete, false diagnostic summary on stdout when phase results are absent or candidates were skipped after a failed initial control. It reports existing process identities/hashes and missing/skipped roles without inventing phase success or creating a summary file. Without that flag, a summary is saved only when the inspection directory already exists. Both controls and all four distinct successful capture phases remain required for `diagnostic_complete=true`.

## Replay and current evidence

```sh
python -B re/tooling/sw2026/oblique_mass/ObliqueMassShape.py replay --controls /frozen/FirstMassPacket/Inspection --output /unused/ShapeReplay.json
python -B re/tooling/sw2026/oblique_mass/InspectObliqueMass.py prepare --baseline /frozen/FlipPacket --predecessor /frozen/FirstMassPacket --mass-metadata /declared/MassApi.json --output /unused/SecondMassPacket --guest-root '\\Mac\Home\Documents\Research\SecondMassPacket' --guest-python 'C:\verified\python.exe'
```

Two independent host processes replayed the six actual calls and produced identical receipt SHA-256 `da21ba9aba7017c42a9a17bfc3971c34025b43be848f47b232d43bb3e24f4ad9`. Six malformed-input process calls were refused. The documented twelve-field CLI shape was accepted separately. Two fresh packet verifies passed. The no-file summary returned incomplete status for both an empty inspection and copies of the actual two failed controls, with F01/F02 explicitly missing/skipped and no summary file created. All sixteen original source tools, original inputs, failed results and analytic predictions remain unchanged.

Second-packet trial SHA-256 is `585b7f475f757c8662234d7916a8c3b515d5c657eab9c4903e01ff30beaca414` and the recipe is `a20aae5e6d6176022b621352e60929d8620b64f06e4b14c379082e70d9bfac80`.

## Native accuracy comparison

Four fresh processes completed the two native controls and two disclosed source diagnostics. All twelve document calls returned status 0 and the measured thirteen-element form. The body API independently returned the same body measurements before and after the accuracy calls. The original shape predictions and tolerances remained fixed.

| Source | Default volume error | Maximum-accuracy volume error | Maximum-accuracy area error |
| --- | ---: | ---: | ---: |
| F01 | −31.441 ppm | −5.074 ppm | −4.307 ppm |
| F02 | −85.336 ppm | −5.416 ppm | −4.511 ppm |

The maximum-accuracy request reduces the discrepancy while both measured sources still fail the original geometry gate. The trial did not enter source edits, save or fresh reopen. [Controlled native accuracy receipt](../measurements/2026/ObliqueCylinderMassAccuracyNative02.json)
