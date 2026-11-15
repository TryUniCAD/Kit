# Read preferences back after changing them

## Expected

`ISldWorks.SetUserPreferenceToggle` returns a Boolean success status that an
oracle wrapper can require before creating a document.

## Observed

The exact 2026 oracle returned `None` for setting input-dimension preference 10
to false, and again for restoring its original false value. The first curve
source preflight incorrectly interpreted these void returns as failures. Both
independent control phases stopped before creating a document. No curve corpus
or lock was produced.

The installed executable was `34.5.2.0604`, with SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
The wrapper revision was `f5d5a4b44`; the failed native records remain in the
owner-controlled `CurvesPreflight01` batch. The
[API method](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISldWorks~SetUserPreferenceToggle.html)
belongs to the application interface. The [installed 2026 type-library
descriptor](../../../../../re/solidworks/v2026/evidence/CurveAuthoringTypeLibrary.json)
confirms `VT_VOID` (24), with two input arguments and no returned Boolean.
Do not infer its return type from similarly named document or extension methods.

## Workaround

Record the setter's actual return value without testing its truth value. Query
`GetUserPreferenceToggle` after the change and require the requested value. Do
the same after restoration in `finally`. An exception, unavailable read-back,
or mismatched read-back remains a failure. A void return alone proves neither
success nor failure.
