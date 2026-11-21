# Required COM output arguments in the oblique source observer

Task `B04-SW2026-FREECAD-CYLINDER`; owner `/root/assembly_occurrence`; delivery PR #121. Native packet01 failed in the observer before mass, independent driver edits, save or fresh reopen. Both known controls passed. This tranche prepares an observer-only retry; it neither repairs the author geometry nor qualifies native source or generated acceptance. [Sanitized receipt](../measurements/2026/FreecadObliqueCylinderObserverRetry01.json) · [Original author workflow](FreecadObliqueCylinderAuthoring2026.md) · [Typed-output gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Primitives/ObliqueExtrusionOutputsRequireTypedInvoke.md)

## Actual failure and registered binding

The author reached `IExtrudeFeatureData2.GetDirectionReference` after creating the two angle planes, height-limit plane, real reference axes, radial-driven circle and the type4 extrusion feature. The first failure was `DISP_E_PARAMNOTOPTIONAL`, signed HRESULT `-2147352561`. Its actual receiver class was dynamic `win32com.client.CDispatch`. Inspecting the generated class's optional-looking Python arguments in metadata did not make that receiver a generated typed caller.

The raw author receipt is SHA `a37ee38c396be766b8de364994d6d21913087b1372b6cf41249fedc1fc5e3c3a`; registered metadata SHA `7b9f4a4b54317d00788568f62debfeb2629f828e37ba2af0c7930201985eccc6`; successful metadata-progress SHA `405911cf036b162fc95c9f60c4f78f53513c02dc710db7cc9cdf7cc303e242c3`. These are disclosed observations only. No hidden source was read.

| Method                     | DISPID | Result      | Required arguments                            | Explicit InvokeTypes descriptors          |
| -------------------------- | -----: | ----------- | --------------------------------------------- | ----------------------------------------- |
| `GetDirectionReference`    |     50 | `I4`        | Four output pointers, dispatch/I4/dispatch/I4 | `(16393,2),(16387,2),(16393,2),(16387,2)` |
| `GetEndConditionReference` |     44 | `IDispatch` | Input `Forward` boolean and output I4 pointer | `(11,1),(16387,2)`                        |

These numbers are independently derived from actual registered descriptors: pointer kind `VT_PTR=26`, underlying dispatch `9` or I4 `3`, parameter flag `FOUT=2`, and `VT_BYREF=16384`. Forward is `VT_BOOL=11`, `FIN=1`. The binding helper admits only these exact two declarations and refuses changed IDs, types, flags, result descriptors or input counts.

The repair invokes `_oleobj_.InvokeTypes` with those actual typed descriptors. The direction call passes no input values but supplies all four output declarations; the end call passes `Forward` and its output declaration. Returned tuple order stays result first, then the actual declared output argument order. Native dispatch outputs are wrapped before the existing explicit interface query. No output value or model state is fabricated.

This follows the primary [pywin32 InvokeTypes implementation](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/PyIDispatch.cpp): declared output parameters are allocated even when the Python caller supplies no initial value, and result/output values form the returned tuple. The new helper also exposes a source-only CLI that reads an actual registered metadata receipt and emits the bounded invocation plans without importing COM or calling SOLIDWORKS.

A separate host filesystem omission was present: `Recorder` was constructed before the `Disclosed/<case>` directory existed. The retry creates that specific raw-record parent first. It does not change the frozen original packet or its results.

## Real measurements retained before failure

The two clean native controls have receipt SHAs `103ae16f087729edd79d8f6a318357f2930153298edcf140ea313489fa3ba462` and `74ea676b13ae71fc2f33f5d44df3b321a96323ca054b34491e8870ac896fe38b`. Their distinct process creation identities bracket the failed author process. The measurement receipt retains those identities, actual control geometry and warning state.

The author read four actual, editable, driving parameters with their own display bindings: angular `D1@TiltPlaneA=0.2173`, angular `D1@TiltPlaneB=0.4879`, linear `D1@HeightLimit=0.02371` and radial `D1@CylinderSketch=0.00743`, in native SI units. Display kinds were angular `3`, linear `2` and radial `5`. Both angle features reported public Type `7`, Type2 `11`, with constraint slots `[16,4]` and actual references. These public properties do not prove a concrete archive runtime class because no native source file was saved.

The full circle was ordinary, non-construction and centered at zero. Actual hinge directions were `-Y` and `+X`, while the initial analytic author protocol assumed the opposite directed hinges. The measured angular normals were `(cos(a),0,+sin(a))` and `(0,cos(b),+sin(b))`. The actual intersection-axis unit was approximately `(0.19141832711339932,0.46010367736252455,-0.8669853690360579)`. These are real partial geometry observations; they contradict the frozen positive-Z tilt-slope expectation. The original prediction is preserved as a refuted direction hypothesis, not rewritten as a pass.

The extrusion definition reported forward end `4`, reverse end `0`, no second direction, no reverse/draft/thin flags and reported forward depth `0.0`. Its actual parent rows retained the profile, Front support, height plane and direction axis. No body count, mass, independent driver edit, native save or fresh reopen had been measured when the observer failed. None is inferred from a nonnull feature or successful rebuild call.

## Frozen retry boundary

Packet02 changes only the invocation helper, its two observer call sites, raw parent creation and the tool closure containing the new helper. The original neutral cases, predictions and healthy control are byte-identical. In particular the original sign mismatch is deliberately retained and may become the next strict failure once the getter is measured. A future hinge-aware positive/negative-flip author design is separate and cannot replace either original expectation silently.

Host verification checks the real frozen filesystem/code boundary. Two independent metadata-plan processes agree; a changed output flag refuses without creating an output. The complete retry packet passes its frozen `verify` command. AST/compile and formatting are static checks. No mocked COM object or fabricated native return establishes success. The actual corrected InvokeTypes call still requires the root-owned oracle.

The original packet, prior API packet and all existing raw receipts remain unchanged. Later sealed-source generation stays disabled. Root alone operates the VM, retries actual native phases and decides source-lock or writer acceptance from their results.
