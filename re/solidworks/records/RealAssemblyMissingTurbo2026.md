# Original V8 assembly needs its missing turbo source

The strict path-based design read of `ENSAMBLAJE DE MOTOR V8.SLDASM` stops at its
unavailable nested assembly mate source. The disclosed comparison independently
opens `Turbo Assy KF.SLDASM` as its own assembly and resolves eleven linked
documents. The older parent requires a different file, configuration and
occurrence graph. [Reproduction receipt](../measurements/2026/RealAssemblyMissingTurbo01.json)

Task `B04-SW2026-CORPUS/REAL-ASSEMBLY-TURBO`, owner `/root/release_path`, delivery
PR #121. The exact missing owner and unchanged strict refusal are verified. A
normal fully linked read of the older engine still depends on the original
turbo source and its own mate records.

## Actual dependency identity

The version-11000 engine has SHA-256
`c1057dd8cf88808c017376e6f04bd50418bd9797f2ffb1d811a5836289b17a10`.
Its ComponentTree stores the file path
`D:\Archivos de diseño\Archivos_Motor_V8\TURBO\ENSAMBLAJE TURBO.SLDASM`.
The expected child file row has local reference 335 and creation time 1547285018.
Model 334 names configuration `Predeterminado`, ID 0, change stamp 905. Active
occurrence 333 uses feature 1556. The parent has 33 children recorded under that
model, including sixteen formed hex screws and four grade-B hex bolts.

The available KF assembly has archive version 14000, creation time 1641581171,
configuration `Default`, ID 0, and root change stamp 293. Its thirty recorded
children include seventeen grade-B hex bolts. Its physical file SHA-256 is
`c4b8f680d8bf3f20450c0c497991d251282b09f007290054cd963413b405c262`.
Connecting the actual in-memory graphs with the existing nested mapping
functions also fails at `RUEDA DE TURBINA-1`, which has zero root mappings.
This check leaves the files and resolver unchanged.

The exact original path is absent from the two equivalent original fixture
import trees, the pinned current tree and its tracked automation manifest.
A reachable-history basename search and the local Kit example and disclosed
research inventory searches found no original file or named project package.
No archive bytes establish a missing-child hash, so the resolved identity
above describes the parent's recorded file row and graph.

## Reproduce the strict read boundary

Use the source tree of `3b5caa3b599b2184f32260e8b383d15044946d5f` and the
disclosed tracked example folder. The tool reads both original Git-pinned
archives through the unchanged SDK, compares the actual nested mapping and
preserves the expected strict result. The current result carries no native
write, roundtrip or corpus credit.

```sh
python3.14 -I -B re/tooling/sw2026/ProveMissingTurbo.py
```
