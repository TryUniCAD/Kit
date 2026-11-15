# Creo oracle notes

## Environment

The local oracle is Creo Parametric 2027.2.0.0 on Windows 11 ARM under Parallels Desktop.
The installation is licensed and is used only for research and acceptance measurement.
Production code does not import or launch it.

## Control procedure

1. Start Creo in a fresh process.
2. Open the vendor empty-part control.
3. Confirm the model tree shows the default datum planes and coordinate system.
4. Record the process id and the visible model name.
5. Close the process before the next candidate.

The control used here was `solid_start_part_mmks.prt` with SHA-256 `b1374d7d356830300a8a4736b6f59a0ba5ef60938398a707fab02e69454aa`.
It opened with `FRONT`, `TOP`, `RIGHT`, and `DEFAULT_CSYS` in the model tree.

## Observed results

| Candidate | Result | Meaning |
| --- | --- | --- |
| Vendor empty-part control | Opened | Oracle and control are healthy |
| Hand-built legacy ASCII part | Rejected; Creo exited | Legacy ASCII is not a usable writer target for this release |
| Synthetic PSB container | Not opened | Container framing alone is not a valid model |

The synthetic PSB test is a parser fixture, not a vendor acceptance candidate.
It has no native model records.

## One-feature ladder

The first ladder rung was authored in the same Creo 2027.2 session from the vendor empty-part control.
The model is a rectangle on `TOP` extruded as a solid with the default blind depth.
It was saved as `ladder1.prt.2` with SHA-256 `8de8280f17552caa406685845d6160195cb8b3a3d4e36fb5510c94a21d647762`.
The retained copy is `re/creo/oracle/ladder/ladder1.prt.2`.

The ladder is a research control, not a writer output.
It proves the oracle can author a live feature tree and a solid body, and it gives the first paired
empty-versus-feature corpus for field localisation.

### Section diff against the empty control

The empty control has 52 sections; the ladder has 57.
The ladder adds `FeatDefs`, `MdlRefInfo`, `IdsGenAllRepsDb`, `IdsGenSimpRepDb`, and `SldRegenRevInfo`.
The sections that grow most are the ones that carry the new feature and its geometry:

| Section | Empty bytes | Ladder bytes | Delta |
| --- | ---: | ---: | ---: |
| `AllFeatur` | 3489 | 7849 | +4360 |
| `VisibGeom` | 42 | 2910 | +2868 |
| `BasicData` | 7549 | 8232 | +683 |
| `BasicText` | 573 | 1014 | +441 |
| `NeuPrtSld` | 918 | 2454 | +1536 |
| `MdlStatus` | 10301 | 13573 | +3272 |
| `SolidPersistTable` | 1144 | 1637 | +493 |
| `BasFullData` | 69 | 1672 | +1603 |
| `IndentTag` | 1361 | 2325 | +964 |
| `THMB_IMG_MAIN` | 597 | 7863 | +7266 |

`AllFeatur` and `VisibGeom` are the primary targets for the feature and geometry field maps.
`THMB_IMG_MAIN` is a derived preview and must not be copied into a writer output.

### Compression anomaly

`DispDataTable` is the only section that fails the current Unix-compress decoder in the ladder.
Its body starts with `1f 9d 10 e0 3b ...`; the first nine-bit code is `480`, which is outside the
initial 256-entry table.
The empty control's `DispDataTable` starts with `1f 9d 10 e0 1e ...` and decodes.
The ladder section is display data, not feature or geometry data, so it does not block the design
decode, but the decoder must not be treated as complete until the variant is understood.

## ARM64 note

Creo is an x64 application.
On Windows 11 ARM, the startup profile must declare the x64 processor environment before the application starts.
Without that declaration the launcher exits before the model window appears.
This is an environment requirement, not a format rule.

## Acceptance still required

A future writer must produce a fresh part with:

- a live feature tree;
- at least one solid body;
- measured volume and centre of mass;
- a driving dimension edit and rebuild;
- a healthy control before and after the candidate.

No such result exists for this change.


## Trail replay (corpus generation)

The playbook asks for a ground-truth corpus produced through the vendor. Creo records every session as
`trail.txt.N`, so replaying a trail would let us save parts without touching the UI. Three attempts were
made.

The option names exist in the binary:

```text
-uitrail
-uitrailin
-uitrailout
```

A hand-written trail was built from a recorded one:

```text
!trail file version No. 2952
#PART
#RETRIEVE
\\Mac\Home\Documents\creo-authored\auth42.prt
~ Command `ProCmdModelSave`
```

| Invocation | Result |
| --- | --- |
| `parametric.exe -g:no_graphics <trail>` | Creo starts, the argument is not treated as a trail; no replay |
| `parametric.exe -g:no_graphics -uitrail <trail>` | Creo starts and exits with no recorded commands |
| `parametric.exe -g:no_graphics -uitrailin <trail>` | same |

In every case the new `trail.txt` holds only the session preamble, with no `#PART`, `#RETRIEVE` or model
`Start` line, and no `auth42.prt.1` is written. So the option is recognised enough for Creo to start and
exit, but the replay never executes the trail. Passing a UNC path may be the problem, or the trail needs
the exact recorded preamble rather than the four-line form.

Until that is solved the corpus step cannot be automated headlessly, which matters because the schema
payload rows — the mask vector and the `ND:*` token tables — can only be shown to be model-derived or
fixed by comparing several saved documents.
