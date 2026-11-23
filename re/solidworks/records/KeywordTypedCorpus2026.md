# Typed SOLIDWORKS part and assembly keyword index

Task `B03-SW2026-KEYWORDS-MODEL/corpus`, owner `/root`, delivery
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The reference is
`9dca0bd65a4762962b0d71b896cdd354eb405a98`. The version-19000 source
groups are the 100 disclosed part and assembly files at that revision
and the 111 independently captured, manifest-pinned cuboids. The model
reuses the existing keyword framing and typed projection. The exit for
this increment is exact typed source replay and exact unchanged ordinary
and nested generation. [Existing model](KeywordModelSlice2026.md) ·
[Recovered source bracket](../FeatureLadderRecovery/README.md)

| Field or record | Classification | Role and recovered encoding |
| --- | --- | --- |
| Root `id`, `Name` | Event input, title input | The unsigned event uses the actual selected header owner. All eight disclosed assembly indexes match the self-reference's shared `f28`. The generated assembly writer binds that scalar directly. |
| Configuration `id`, `Name` | Derived identity, name input | Each of the eight assembly rows joins the selected CMgr `f360` node's actual ID and name. The declared type is `ConfigurationManager`. Optional material is a presentation value with distinct absent and empty states. |
| `Feature`, `Sketch`, `Extrusion` | Format vocabulary and derived identity | A row keeps its allocated ID, name, tag and type when present. The saved corpus has 23 dissectable type-less sketch rows with no dimension entries. |
| Empty sheet-metal master | Reserved helper identity | All 31 saved `Feature` rows with ID `-1` have an empty name, no children, and type `Sheet-Metal Master`. The actual Config-0 `f1018` owner has the matching ID, absent name and empty data. The marker is not an allocated user feature. |
| Dissection fields | Derived relationships and lexical order | A single child ID refers to an emitted feature. All eight observed type-less cuts store `DissectableChildren` before `DissectableRoot`. Existing publication profiles also use the reverse attribute order. The source reader checks the observed order and reconstructs the matching grammar from typed fields. |
| Dimensions | Display input, format modifier | The numeric value and fractional places encode the visible decimal, without retaining its lexeme. Plain values, suffix `°`, prefix `R`, and prefix `<MOD-DIAM>` have distinct typed representations. The XML layer escapes the diameter tag in text. Raw parameter units, formula, precision choice and model magnitude remain properties of the dimension and display owners. |
| `Reference` ID and name | Derived identity, occurrence input | All nine stored rows match the actual binary occurrence ID and visible occurrence name. |
| `Reference.Type` | Derived linked-file display token | The field is the target leaf stem followed by `-`. All nine saved tokens match the binary file owner's `h10` name. Its `h18` physical path is redacted in the disclosed files. Ordinary and recursive generated assembly builders retain their existing physical leaf rules and derive each occurrence's token from its own resolved child. |
| Tag grouping and framing | Derived order, format vocabulary | The ordinary assembly projection orders tag names and decimal ID strings lexically. The classified reader preserves the actual row order. It independently verifies the complete native framed XML, including compact and spaced empty elements. |

The [new audit](../../tooling/sw2026/AuditKeywordModels.py) reconstructs
the stream from typed rows. The source comparison rejects unsupported
attributes, row types, numeric spellings and mixed cut orders. It
measures the separately decoded configuration, timestamp, occurrences
and empty sheet-metal owner. The ordinary and nested regression workers
receive neutral data only. They compare the complete generated files and
all streams with the former production source tree. The two nested
requests are checked against their existing disclosure pins.

The [receipt](../measurements/2026/KeywordTypedCorpus01.json) records 211
exact indexes and 309 dimension rows, including 39 radii, 31 diameters
and four angles. All eight assembly configurations and event values,
nine occurrences and 31 empty sheet-metal markers join their independent
binary owners. The 18 ordinary and two nested neutral inputs reproduce
43 complete files and their streams. The 40 guarded worker processes
record zero runtime writer input reads.

```sh
python3.14 -I -B re/tooling/sw2026/AuditKeywordModels.py \
  /absolute/path/to/verified-baseline-worktree \
  /absolute/path/to/disclosed-captures /tmp/UnusedKeywordModels.json
```

Saved full-source keyword generation still needs to join the native
assembly's resolved environment state to its actual containing owner.
The same environment node appears in both binary views on all eight
disclosed files, but its saved owner representation differs from the
fresh construction graph. Resolving redacted physical links and deriving
display precision for every source document also remain separate from
this typed stream comparison. There are no new SOLIDWORKS launches or
held-out feature claims in this audit.
