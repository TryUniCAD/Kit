# SOLIDWORKS exchange database framing

Task `B04-SW2026-ASSEMBLY-EXCHANGE`, delivery
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The standalone
part and assembly exchange tools share one physical UnQLite writer
and a reader for the observed single-bucket Windows layout.
[Pinned upstream UnQLite 1.1.9 source](https://github.com/symisc/unqlite/blob/ddb1687036d207bbfc67b98cb470fe52ddf22f62/unqlite.c)
· [Guarded receipt](../measurements/2026/UnqliteExchangeStore01.json)

| Field | Classification | Construction or interpretation |
| --- | --- | --- |
| Pager signature, sector size, page size, engine | Format constants | The observed files use the UnQLite magic, 512-byte sectors, 4,096-byte pages and the `hash` engine. The engine name contributes its byte length. |
| Database creation word | Volatile event with computed format | Pack the explicit creation time in the UnQLite DOS layout with a zero-based month and two-second resolution. The measured files share this word across both databases within one save. Across the first eleven inputs, the database creation event follows the archive header save time by 0 to 27 seconds. |
| Linear hash map | Derived allocation metadata | Hash the engine probe word, initialize the unsplit table and map logical bucket zero to physical page two. |
| Active cell header and contents | Derived framing and model record input | The key and value lengths, key hash and previous-cell link follow from each emitted record. On a source read, follow the stored live links in either offset direction and retain the reverse traversal as the insertion order. |
| Free list and padding | Derived free extents and volatile old storage | The scoped saved headers have one free block. Saved model databases have three, with 64 to 423 nonzero inactive bytes across the first eleven files. The reader validates range coverage and disjointness. The fresh writer constructs consecutive live cells and a zero-filled tail with one computed free-block header. |

The decoder validated all 108 live records in twenty-four disclosed
assembly databases and reconstructed each logical store with fresh
placement. Twelve configuration-header databases matched every saved
byte. The twelve model databases matched their creation clocks and
complete ordered live records through fresh placement. Their saved free
regions contain historical residue. Construction never consumes
that residue. The independent pinned UnQLite engine read every
generated store back with the same keys and values.

Four stdin-only workers independently generated two fresh stores with
different authored record counts and months. Both read back through
the reference engine. Malformed map, key hash, link-cycle and
allocation controls refused. The writer reported zero runtime input
reads. The earlier part configuration and object exchange replays
retain their exact receipt hashes. The historical replay wrapper keeps
its established packed-clock argument behavior.

The [configuration name ownership record](ComponentNameOverrideStorage2026.md)
identifies separate application-level requirements for the actual
MessagePack entries. The physical verification adds zero SOLIDWORKS
launches or held-out qualifications.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveUnqliteExchangeStore.py \\
  --disclosures /absolute/path/to/Oracle121Takeover \\
  --reference-library /absolute/path/to/libunqlite.dylib \\
  --reference-source /absolute/path/to/unqlite.c \\
  --output /tmp/UnusedUnqliteExchangeReceipt.json
```
