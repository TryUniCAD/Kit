# Internal thin revolve construction on principal planes

Workstream `B04-SW2026-REVOLVE-THIN`, delivery PR #121. The portable `ThinRevolve` definition binds one explicit angular sweep and one or two feature-owned positive wall drivers. SOLIDWORKS preparation supports the bounded forward partial open axial line and independent ordered construction axis on the three canonical principal frames. Public writer admission stays closed pending independent native comparison. [Front construction and comparison](ThinRevolveConstruction2026.md) · [Field ownership](ThinRevolveWireOwners2026.md)

## Exact disclosed evidence

Two independent SP05.2 sources and their edited derivatives bind the Top opposite and Right mid-plane support frames. Their disclosed source lock hashes to `7475170f6f524ba33fe826b54976f7d2793c9bd603851d1a31866220d26c6253`, with spec SHA-256 `72341240e566c2fe027716478fa3e07b389cf4e5451e463f3c14698afe23e694`. Their acquisition passed eight distinct native processes with healthy brackets. The before and after files re-emit both load-critical typed configuration and resolved streams.

| Support and wall | Native source SHA-256 | Edited native derivative SHA-256 | Wall carrier basis |
| --- | --- | --- | --- |
| Top opposite | `856e9ef1568469bbe54d0418918d79bd6998b76ae552775dbe77e3d775450721` | `21f46c077d21ce1f66a73720f9677daff1ac88f4aa183235c24351e31aed8d05` | −X, −Y, +Z |
| Right mid-plane | `4220ae33c17a2d6f1fda6bd81769dda049544e00acab9633f1acdf068011875c` | `ce3a4303b3265fab59837ba61801138c8e0efaf23921c68fe42a8965b01e4259` | −Z, +X, −Y |

The authored line and axis incidences remain in sketch coordinates. The selected native line reference stores the axis origin and direction in the model frame. Each active wall dimension's endpoint fields `f80` and `fa0` store the radial span at its actual axial midpoint in model coordinates. `fe0` is the signed radial axis and `fe8` the signed support normal. The `ff0` inverse frame uses the signed support U, signed support normal, and negative support V axes, with the first world endpoint determining translation. This rule reproduces all four observed native wall frames and preserves the four previously measured Front output bytes. Inactive D4 stays zero and unplaced. The cold profile retains the initializer state and omits saved body, radius display and face caches. [World-space wall carrier gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/ThinWallAnchorsAreInModelSpace.md)

## Freeze a disclosed comparison

The host collector compares every newly observed axis and active wall frame to the actual saved geometry using an independent frame calculation. Eight isolated generation workers reproduce the four exact native-tested Front files and generate the two principal candidates twice. The worker checks portable model round-trip, all ten generated stream replays, change confinement to the resolved and keyword owners on dimension edits, and refusal of the reverse axis, suppressed sketch and public native output. The guard admits zero runtime file reads.

```sh
python3.14 -B re/tooling/sw2026/revolve/ThinArchive/BuildThinPlanes.py \
  --capture /absolute/path/to/disclosed/NativeCapture \
  --spec /absolute/path/to/disclosed/Spec.json \
  --front /absolute/path/to/prior/DisclosedFrontPacket \
  --output /absolute/path/to/new/Packet \
  --guest 'C:\KitThinPlaneGenerated01'
```

The owner copies this packet to its exact local Windows locator before invoking `py -3.12 -B C:\KitThinPlaneGenerated01\Tools\RunThinNative.py C:\KitThinPlaneGenerated01\NativeJob.json JOB_SHA256`. The matched source and generated edit and fresh reopen phases require ten distinct SOLIDWORKS processes, two healthy controls, clean cold loads, the complete recursively ordered feature tree, actual editable D1 and D3 ownership, and native mass and bounds comparison. The disclosed Top and Right runs supply prospective evidence for these scopes. They do not count as independent held-out acceptance.

[Host preparation](../../tooling/sw2026/revolve/ThinArchive/BuildThinPlanes.py) · [Typed axis and wall proof](../../tooling/sw2026/revolve/ThinArchive/ThinPlaneAudit.py) · [Pre-writer source lock](../measurements/2026/RevolveThinHeldoutSourceLock01.json)
