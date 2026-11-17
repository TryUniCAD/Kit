# Link SOLIDWORKS configuration maps to shared header objects

The SDK archive layer selects the direct external-file objects for an ordinary
version-19000 configuration from its typed model header. Selection visits the
present self file at `f38`, then the `f30` directory in list order. Direct binding
allocates one shared map slot for each selected object and advances the inherited
base to the resulting counter. Existing node identities and standalone header
indices survive this handoff.

`HeaderRefNodes` accepts the graph returned by `ReadHeaderGraph`. Its explicit
directory callback also accepts the research reader's ordered item representation.
The actual research Config load/store uses this shared selector for version 19000.
Its direct map operations delegate to SDK `BindNodesMut` in every existing caller.
The research header reader retains its source spans and schema-usage evidence.
Earlier research versions retain their existing selection path. The drawing's
inline header follows its existing separate wire grammar.

Verify a disclosed ordinary part/assembly pair with the existing header command.

```sh
python re/tooling/sw2026/serial/CheckSdkHeaders.py PARENT CHILD --config-handoff --report UNUSED.json
```

The process uses the actual SDK header nodes when reading and storing Config,
ResolvedFeatures and an available MatesList. It records direct indices, map
counters, occurrence aliases, complete byte comparisons and implementation hashes.
Each selected stream must consume its complete payload. Other SDK header-only
checks use the command's original invocation.

The focused process regression generates a distance-mate bundle under the existing
no-runtime-input-read guard, verifies the linked headers and exercises typed mate
projection. The synchronized-source process also verifies this handoff for all
five disclosed files. The final local run passed five process integrations and
twelve disclosed/generated files with twenty-four header comparisons. All six
prior projection CLI outputs stayed byte-identical. A generated child's linked
field inventory passed strict schema admission and its implementation assertion
verified 89 source fingerprints. Black, Ruff, Mypy, Pyright and the steering
checker passed for the scoped SDK/test source. The receipt binds exact inputs
and implementation hashes.

The supported SDK slice is header selection and map registration for ordinary
version 19000. Production attachment of complete mate graphs still requires
qualified Config and Resolved body grammars. Native conversion acceptance remains
a separate measurement requirement.

[Rules and verification evidence](../../../../re/solidworks/records/ConfigHeaderHandoff2026.md)

[Existing direct-reference ordering gotcha](../../../Gotchas/Conversion/Solidworks/Archive/ExternalReferences/DirectReferenceSlotsFollowHeaderOrder.md)
