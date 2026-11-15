# Creo feature struct in the model module

## Why this page exists

`cr_flags_xar` is the field that blocks `AllFeatur` authoring, and it
could not be reached from the container modules: `strings` finds `Sld_Features` and `first_feat_ptr`
in `coreutils_sh.dll`, `metatoolsapi.dll` and `diagexport.dll`, but not `cr_flags_xar`.

The field name does exist in the model module. This page records where.

## Locating the module

The model executable is not under `Parametric\x86e_win64`, which does not exist in this install. It is:

```text
C:\Program Files\PTC\Creo 2027.2.0.0\Common Files\x86e_win64\obj\xtop.exe
```

Copied out of the guest to `~/Documents/creo-re-bin/xtop.exe` (326,650,848 bytes), outside every
repository checkout. It is researched, never shipped.

## What the model module contains

Exact-name matches in `xtop.exe`:

| String | Count |
| --- | ---: |
| `cr_flags_xar` | 1 |
| `cr_flags` | 1 |
| `Sld_Features` | 0 |
| `first_feat_ptr` | 1 |
| `next_feat_ptr` | 1 |

So the container module and the model module split the format between them: the container module reads
the section framing and the linked-list *skeleton*, the model module owns the feature *struct*,
including the mask field.

## The feature field-name table

`cr_flags_xar` sits at file offset `0xe7c2220`, inside an ordered pool of feature-struct field names.
Scanning the 8 KB window `0xe7c1000..0xe7c3000` yields 423 names, including:

```text
par_size, par_id_tab, dtm_id_tab, more_cr_flags, gerrors, proc_gerrors, save_geoms,
cr_flags_xar, cvt_feat_dat, feat_dates_ptr, comp_hist, bkp_id_tab, body_hndl_id_tab_ptr,
...
taper_info_xar, boundary_obj_xar1, overl_info_xar, matrix2, ids_inserted, ids_removed,
geoms_affected, edgs_affected, qlts_affected, los_affected, sld_bodies_affected,
-edge_refs, geom_refs, lo_refs, sld_body_refs, -dummy_mrg, -dummy_smtl,
...
```

Two things in that list matter:

- `more_cr_flags` is a separate field from `cr_flags_xar`, so the mask state is split across at least
  two members and a single array is not the whole story;
- `-dummy_*` entries are placeholders, so the table is a *compiled-layout* inventory rather than a
  clean schema.

Entries are variable-width and NUL-padded to 8 or 16 bytes (`save_geoms\0\0\0\0\0\0`), so the pool is
not a fixed-stride array. The descriptor array that pairs each name with a type and an offset is
elsewhere in `.rdata` and has to be found by cross-reference.

## The descriptor table

The name pool is referenced from a table in the `.ddt` section, which is present in the PE headers
(`va 0x13eb7000`, raw `0x130aaa00`, size `0x4ee200`) and is not one of the standard sections.

Locating it: the string `cr_flags_xar` sits at file offset `0xe7c2220`, which maps to virtual address
`0x14e7c3a20` (image base `0x140000000`). The only 8-byte little-endian occurrence of that address in
the whole file is at file offset `0x133db880`, inside `.ddt`.

The records have a **stride of `0xd0` (208 bytes)** and the name pointer is the first field:

| field | name | record offset |
| --- | --- | ---: |
| `more_cr_flags` | `0x133db540` | index 246 |
| `save_geoms` | `0x133db7b0` | index 250 − 1 |
| `cr_flags_xar` | `0x133db880` | index 250 |
| `cvt_feat_dat` | `0x133db950` | index 251 |
| `feat_dates_ptr` | `0x133dba20` | index 252 |
| `comp_hist` | `0x133dbaf0` | index 253 |
| `bkp_id_tab` | `0x133dbbc0` | index 254 |

Walking the stride while the record stays valid gives the table extent
`0x133ced60..0x133f40f0`: **734 entries** over **514 unique names** (`type` appears 13 times, `id` and
`name` five times each, while `cr_flags_xar` appears exactly once).

## What the table does not contain

Each record holds only two non-zero words:

```text
+0x00  name pointer
+0x04  1
```

Every other column is zero across all seven fields above. So this is a **name registry**, not a layout
descriptor: it proves which field names the model module knows and fixes their order, but it carries no
type and no struct offset.

Two consequences:

- the feature-struct offsets for `cr_flags_xar` and `more_cr_flags` are not in this table, so they have
  to come from a parallel array or from the code that indexes the struct;
- `cr_flags_xar`'s table index is `250`, and the empty control's mask array has `252` slots. That is
  close enough to be worth testing as a hypothesis — one slot per registered field plus two — but it is
  not established, and it does not explain why the ladder control's array has `311` slots.

## Next

The path is now name-based again, in the module that owns the struct:

1. find the feature-struct offsets of `cr_flags_xar` and `more_cr_flags`, which are not in the `.ddt`
   name registry;
2. follow the model code that reads those offsets to learn which bit gates which field;
3. test the index hypothesis, `250` against `252` slots in the empty control.

Step 1 needs a full analysis of a 326 MB PE. That is the remaining cost, and it is a different order of
effort from the section-grammar work: not another emitter tweak.
