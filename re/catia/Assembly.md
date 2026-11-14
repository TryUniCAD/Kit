# CATIA CATProduct assembly

## What is decoded

The `Data` stream contains an `ASMPRODUCT` table. The table has a root name, `_Reps` boundaries,
definition names, instance names, and `IsRoot` markers. The reader resolves component source paths
through the sibling `.CATPart` and `.CATProduct` directories.

The three-product corpus decodes:

| Product | Tokens | Instances |
| --- | ---: | ---: |
| `Brake_Pedal_Assembly - Backup 1` | 100 | 48 |
| `Brake_Pedal_Assembly - Backup 2` | 37 | 7 |
| `Tilton_Set` | 38 | 4 |

## What is not decoded

Occurrence transforms and assembly constraints remain native-only. The reader records
`catia.product.transforms_unresolved` and `catia.product.constraints_unresolved`. It does not invent
identity transforms as measured values.

## Evidence

- `src/convert/adapters/catia/Assembly.py` decodes the product table and component references.
- `tests/convert/catia/CatiaAssemblyTests.py` covers the three-product corpus.
- `CATObjectModelerBase.dll` SHA-256 `a522a0a040c74fc8f53aea707785e0d00e836d9eb8a113a25349fbd985905980`.

## Open work

1. Decode occurrence position records.
2. Decode connector and constraint records.
3. Emit a native CATProduct with occurrences and transforms.
4. Measure the assembly in CATIA.
