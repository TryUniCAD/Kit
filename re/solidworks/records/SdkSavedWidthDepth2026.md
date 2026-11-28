# Active body ownership in one saved width-depth part

Task `B04-SW2026/equations-saved-body`, owner `format_proofs`, delivery PR #121.
The exit condition is matching the actual active body, editable history and
measurements in both public read modes for the disclosed saved Front Plane
width-to-depth boss. This reader slice depends on the existing relation-aware
configuration and resolved graphs, the saved partition decoder, and the
ordinary active atom and kernel body rules. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Research playbook](../../Playbook/README.md)

The prior [native lifecycle](../measurements/2026/SdkWidthDepthPreparationNative01.json)
records SOLIDWORKS `34.5.2.0604`, six distinct processes, two healthy controls
and the native edited reference SHA-256
`320adbeeb193227fb8c0b03f7278ac7cf91d421d82da68fecb27416dc03db393`.
The measured case has driving sketch D1 and D2 of 47.875 and 17.375 mm.
Its active boss D1 is 23.9375 mm and follows the single local equation
`"D1@Boss-Extrude1" = "D1@Sketch1" / 2`.

The saved Config relation is `moRelation_c` slot 62 at `[3258,9955)`.
The dependency uses live sketch dimension slot 128 in Config-0
`[7133,7248)`. The target uses live feature dimension slot 313 in
ResolvedFeatures `[7975,8086)`. The retained Config and Resolved map
counters are 198 and 338. The name reader uses this same linked map to
join the actual output atom at Config-0 slot 58 `[3096,3196)` to the manager and
active partition. The observed atom manager ID is 101. The reported
`BODY_MATCH` is 1422, and rollback marks are 8 and 2. The decoded active
partition has 177 typed nodes. The selected body is index 2, and its
implicit name `Boss-Extrude1` and final producer ID 21 come from the
verified native ownership graph. These values describe the measured
file. The reader derives its owners from the input.

The complete stored boundary uses six planar faces with outward rings,
twelve line edges and eight vertices. Five carrier directions oppose the
outward rings and have reversed face sense. The reader checks that sense
and trim incidence, then compares all oriented rings exactly against the
prism computed from the linked sketch and live depth. Shape validation
keeps the selected native partition as the source of the exposed B-rep.
The full and design-only reads retain the same 19 features, editable
parameters, body owner and geometric summary. The full read retains
three native payloads. The design-only read omits the public B-rep and
payload attachments. The body volume is 19911.8857421875 mm³, its area is
4787.5 mm², and its centre is (23.9375, 8.6875, 11.96875) mm. These five
coordinates and measures agree to six significant figures with the prior
native result.

The independent saved plain cache came from the same rectangle with an
ordinary 19.5625 mm depth. Replacing just the selected partition in an
in-memory contrast leaves all other logical streams exact. Both strict
read modes refuse its physical boundary, and permissive modes retain
the diagnostic and omit the unbound B-rep. A separate typed caller
contrast points the already-read relation at the actual sketch owner
instead of the actual body creator and receives the owner refusal in
both modes. Neither contrast is sent to SOLIDWORKS or emitted to disk.
Three control inputs retain both complete neutral JSON digests from
`d3f98794746cb3e63b9db4710e08399312daf4ee`. The controls are the cold
related part, the cold plain part and the native-saved plain part.

Run the [offline proof tool](../../tooling/sw2026/equations/ProveSavedWidthDepth.py)
with the disclosed `WidthDepthSameLocator04` packet directory.

```sh
python3.14 -I -B re/tooling/sw2026/equations/ProveSavedWidthDepth.py \
  --packet /path/to/disclosed/WidthDepthSameLocator04
```

The [proof receipt](../measurements/2026/SdkSavedWidthDepth01.json) binds
the prior native result and all four disclosed file hashes. Five fresh
offline workers receive input bytes over stdin and record zero CAD file
opens. The research CLI's SOLIDWORKS asset workflow requires committed
input blobs, so this check uses the existing disclosed lifecycle receipt
and an offline SDK worker for the external digest-bound CAD files.
[Research CLI asset scope](../../../Documentation/Tasks/ResearchCommandLine.md#decode-committed-inputs)

The saved reference still reports unresolved text properties. Other
relation forms, cached geometries and wider source inventories remain
outside this evidence. This read-only proof adds zero native launches,
held-out results and writing or publication qualifications.
