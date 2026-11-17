# SOLIDWORKS 2026 planar mate endpoint construction

A principal-datum endpoint selects an actual generated child feature and an
occurrence belonging to the containing assembly. For the ordinary one-hop
subgraph, the chain component records that assembly object and its path reuses
the existing external-feature entry of the selected occurrence. Two placements
of the same child file therefore retain distinct occurrence identities.
[Native chain proof](PlanarMateReferenceChains2026.md)

| Field group | Construction |
| --- | --- |
| Selected plane `ff0` | Use the generated datum's persistent ID and its authored creation time. The shared principal-plane constructor provides the native axis discriminator. |
| Chain component and trip through the map | Use the owning assembly and the exact occurrence's `f4f8` entry, including its backlink to that occurrence. The stamp combines the seed 101 and the occurrence's state word. |
| Chain `f20`, `f24`, `f40` | Use fresh detached-copy acquisition state zero, resolved one-hop mode and the shared absent configuration override. Native persistence of this initial acquisition state still needs measurement in a full mate. |
| Resolved reference geometry | The child update stamp and both placement transforms come from the selected occurrence. Apply the child's placement to the datum origin and axes. Compose the inverse from the world plane basis and the negative projections of the world origin. The drawn rectangle comes from the actual child datum's `f6f8.b0..b3`. |
| Detached reference geometry | Keep the world origin and normal. Use the identity transform and zero surface bounds, as observed in the three disclosed mates. |

`PlanarMateEndpointProcess.py` runs the ordinary assembly and child builder from
stdin, seeds the archive with the assembly's actual resolved map and exercises the
typed component and embedded geometry records. The JSON object takes a `bundle`
request and two `endpoints`, each containing `occurrence` (zero-based), `datum`
and `created_at`. The two inputs use the repository's `MakeOccInput` helper and
replace its occurrence list with the lists recorded in the receipt. The output
checks the map and ownership links and requires exact re-encoding.

```sh
python3.14 -B re/tooling/sw2026/PlanarMateEndpointProcess.py < /private/endpoint-request.json
```

The two fresh inputs matched independent plane origins, normals and inverse
transforms. Their encoded records use 922 and 1,210 bytes, with zero runtime
input file attempts. An unknown datum was rejected. The complete mate feature,
selection status, solver, and native load, edit and save remain open. The
generated child for these probes starts with its constructor datum extents.
[Guarded proof](../measurements/2026/GeneratedPlanarMateEndpoint01.json)
