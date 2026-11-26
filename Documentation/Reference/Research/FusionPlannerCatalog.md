# Fusion planner catalogue

## Purpose and scope

The collector saves an indexed SQLite inventory for research planners.
CSV exports expose common inventory slices for inspection.
The catalogue separates API declarations, command observations, native schemas and historical capture evidence.
All authoring, decoding, writing and verification status fields remain `unverified`.

The [hybrid planner proposal](https://github.com/TryUniCAD/Kit/pull/162) can consume these records.
This change supplies data and collection tools, not an implemented scheduling integration.
The [research programme](../../../Roadmap.md) retains its existing ownership and acceptance requirements.

## Saved inventory

The [published bundle](../../../re/Fusion/PlannerCatalog/Data) records Fusion `2706.1.17`.
Its manifest supplies exact counts, source fingerprints and output hashes.

| Inventory                                            | Count |
| ---------------------------------------------------- | ----: |
| API classes across eight definition files            | 2,037 |
| API properties, with merged accessors                | 6,696 |
| Non-dunder methods and package functions             | 4,622 |
| Method and setter parameters                         | 8,406 |
| Enum-like values and other class constants           | 2,144 |
| Commands in the current session capture              | 3,151 |
| Saved command observations, including older captures | 3,225 |
| Native metatypes                                     | 1,958 |
| Native class/version lookups                         | 3,563 |
| Initialized exact own schemas                        |   494 |
| Registered members of those schemas                  | 1,991 |
| Historical authoring scripts                         |   177 |
| Historical ground-truth sidecars                     |   197 |

The current command capture read metadata without executing commands or creating documents.
It recorded 38 workspace identities and 88 unavailable getter results.
Older captures are retained with their filtering and failure limits.

## Files and query interfaces

| File or interface                       | Use                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------ |
| `Data/Catalog.sqlite`                   | Primary indexed planner input                                                  |
| `Data/Manifest.json`                    | Schema, provenance, content fingerprint, counts and artifact hashes            |
| `Data/ApiTypes.csv`                     | All declared API types, including objects outside timeline feature inheritance |
| `Data/ApiOptions.csv`                   | Properties, methods, setter metadata and declared method arguments             |
| `Data/ApiEnums.csv`                     | Enum-like values and other class constants with their owners                   |
| `Data/Commands.csv`                     | Command observations with their capture source                                 |
| `Data/NativeTypes.csv`                  | Registered native metatype inventory                                           |
| `Data/Gaps.csv`                         | Explicit missing, unavailable and unverified evidence                          |
| `sources`, `items`, `relations`, `gaps` | Stable SQL views exposing readable identities                                  |
| `api_effective_members`                 | Own and inherited API members, with overrides resolved by nearest declaration  |
| `api_feature_types`                     | The `Feature` inheritance branch, including its root                           |
| `native_schemas`                        | Version, lookup status and nullable member count                               |

Integer keys and indexes provide compact internal joins.
Readable identity views preserve stable references for planner queries.
API relationships include inheritance, property types, parameter types and return types.
Method argument details preserve declared defaults and unresolved domains.
Documentation markers record textual mentions of preview, retirement or deprecation.
They do not establish the availability of the owning declaration.

## Verify and rebuild

Use a checkout containing the collector and saved research evidence.
Python must provide SQLite JSON functions.
Python 3.14 is used for this saved collection.
The verifier needs neither Fusion nor its API installation.

```sh
uv run --python 3.14 python re/Fusion/PlannerCatalog/VerifyCatalog.py re/Fusion/PlannerCatalog/Data
```

To rebuild, identify the installed API definition directory.
Keep the proprietary installation outside the checkout.
Choose a fresh output directory.

```sh
uv run --python 3.14 python re/Fusion/PlannerCatalog/BuildCatalog.py \
  --api-root "/path/to/Autodesk Fusion.app/Contents/Api/Python/packages/adsk/defs/adsk" \
  --commands re/Fusion/PlannerCatalog/Sources/Commands.json \
  --output /tmp/FusionPlannerCatalog
```

The collector reads API syntax without importing or executing vendor code.
It derives the build from the installation's `Contents/Info.plist`.
Source hashes bind the declaration inventory to that installation.
Vendor code and documentation are not copied into the bundle.
Add `--all-csv` to export every relational view as CSV.
Existing output directories are refused.
Failures remove the collector's temporary build directory.

For a fresh command snapshot, explicitly run `CaptureCommands.py` inside the intended Fusion session.
The script writes `Commands.json` beside itself.
Pass that path through `--commands` when collecting.
Its timestamp and exact script hash remain in capture provenance.
The script does not switch workspaces, execute commands or create design documents.
Full availability across workspaces and licences remains unresolved.

## Planner queries

Open `Catalog.sqlite` with a read-only SQLite connection.
Verify the bundle before consuming it.
Use the stable views instead of depending on internal integer keys.

List editable extrusion input properties:

```sql
SELECT name, json_extract(details, '$.return_type') AS declared_type
FROM api_effective_members
WHERE type_id = 'api:adsk.fusion.ExtrudeFeatureInput'
  AND kind = 'api_property'
  AND json_extract(details, '$.writable') = 1
ORDER BY name;
```

Read the type's methods and their parameter records:

```sql
SELECT m.name AS method, p.name AS parameter, p.details
FROM items m JOIN items p ON p.parent_id = m.id
WHERE m.parent_id = 'api:adsk.fusion.ExtrudeFeatureInput'
  AND m.kind = 'api_method' AND p.kind = 'api_parameter'
ORDER BY m.name, p.id;
```

Count unresolved native schema lookups:

```sql
SELECT lookup_status, COUNT(*)
FROM native_schemas
GROUP BY lookup_status;
```

## Interpretation limits

The snapshot covers extracted declarations and observed evidence, not every legal feature combination.
Method-specific enum subsets, numeric ranges, units and dependencies remain unresolved until independently established.
An enum-like class classification is syntactic evidence, not proof of method validity.
Language protocol methods are excluded from the non-dunder method inventory.

Sketches, constraints, construction geometry and other authorable objects can lie outside `Feature` inheritance.
Use all API types and typed relationships when building family specifications.
A creator-looking method can construct a proxy rather than an independently authored feature.

Absent and uninitialized native schemas have `NULL` member counts.
Initialized empty schemas have an explicit zero.
Historical base versions remain unknown when the capture exposes only a base pointer.
Raw option masks are preserved, with persisted membership derived only from bit `0x1`.
Registered fields do not establish complete wire serialization.

Recipe presence and matching entry-source hashes do not qualify authoring.
Historical helper bindings, reported errors and incomplete capture states remain visible.
API-to-wire mappings and all [CAD success criteria](../Operations/CadSuccessCriteria.md) remain separate requirements.
