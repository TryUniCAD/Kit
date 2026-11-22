# Writing rigid nested SOLIDWORKS assemblies

Kit generates SOLIDWORKS 2026 SP05.2 rigid nested assemblies from a complete millimetre neutral `CadDocument.assembly`. Public writes require exact native measurement of the full generated bundle. Supply an acyclic graph with a root assembly, at least one subassembly, owned rectangular blind-boss part documents and an explicit selected configuration for every definition. Use complete ordered rigid placements. Repeated occurrences of a definition share one native file and retain independent placements.

An owned part uses a rectangular Front-plane sketch and one forward blind boss with driving `D1`. The plain leaf has an unconstrained sketch. The qualified dimensioned rectangle also keeps two ordinary sketch lengths with their actual horizontal and vertical relations. Each active configuration must agree with the configuration selected by its occurrences. Mates, fixed, suppressed, hidden or flexible instances, extra semantic state and incomplete ownership are refused.

The SOLIDWORKS discovery entry lists capabilities across both writer routes. An assembly root carries the owned occurrence graph, root configuration and support planes. Part body and selection data belong to qualified part documents.

Use an unused path whose basename is the assembly's modeled name. The registry selects the writer from `.SLDASM` or the format alias `solidworks.sldasm`. On Windows, the actual absolute output path supplies the native file locator. On another host, pass the corresponding absolute Windows `native_destination` separately from the physical destination.

```python
from pathlib import Path
from convert import write_document

result = write_document(
    document,
    Path(r"C:\Generated\Frame.SLDASM"),
    destination_format="solidworks.sldasm",
    allow_carrier=False,
    values={
        "require_native_transfers": True,
        "solidworks_native_measurement": measurement,
    },
)
```

Supply the parsed offline measurement in `measurement`. Its `written_at` is the bundle creation epoch. Its `receipt` is the associated passing native report in assembly form. The caller establishes the authenticity of the unsigned report. The SDK verifies the native bracket, logical namespace, exact member order, names, configurations, dependency links, lengths and complete SHA-256 hashes before the first staged file write. Both acceptance flags are true after that check for the measured bundle. Missing or mismatched evidence refuses the write regardless of the carrier preference. Prepare a new bundle for measurement through the internal in-memory constructor. [Measurement evidence and export](../../../re/solidworks/records/NestedAssemblyDelivery2026.md#exact-measured-publication)

The CLI accepts the same measurement envelope as a JSON file.

```sh
kit convert Neutral.json Frame.SLDASM --native-measurement Measurement.json \
  --native-destination 'C:\Generated\Frame.SLDASM'
```

On Windows, the final output path already supplies the native locator.

The registry publishes each owned definition beside the root file. It checks for conflicting sibling filenames and rolls back files published by this call if publication fails. Existing files and conflicting aliases are refused. Assembly overwrite and stream output are unsupported.

The result path and `bytes_written` describe the root assembly. The `component_file_count`, `component_file_names`, `component_bytes_written` and `bundle_bytes_written` metadata describe the complete bundle. [Exact native and public evidence](../../../re/solidworks/records/NestedAssemblyDelivery2026.md)

Strict SDK reads recover the measured definition names, local occurrence order,
physical owner titles in expanded paths,
and the three driving limits in each dimensioned leaf. The body is rebuilt
from its actual sketch lengths, support and blind depth. Full publication of
an unprojected native assembly readback remains open.
[Dimensioned leaf readback](../../Changes/Solidworks/Archive/Assembly/SolidworksColdDimensionedLeafRead.md)
