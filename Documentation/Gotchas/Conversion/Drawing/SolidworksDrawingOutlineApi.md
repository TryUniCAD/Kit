# Drawing outline APIs fail under late binding

## Expectation

`IView.GetPolylines5` and `IView.GetOutline` expose projected drawing geometry
that can be dumped from a `cscript` macro and compared with the display-list
streams.

## Actual behavior

On SOLIDWORKS Design Premium 2026 SP5.2:

- `View.GetPolylines5(0)` reports a 75-element array for a simple four-view
  drawing, but every element has `VarType` 0 (`Empty`) under `cscript`
- `View.GetOutline` returns `VarType` 8197 (array of double) and `IsArray` true,
  but indexing element 0 raises VBScript error 13, type mismatch
- PowerShell `New-Object -ComObject SldWorks.Application` plus `OpenDoc` fails
  with `TYPE_E_ELEMENTNOTFOUND` (`0x8002802B`)

The failure is in the late-bound COM marshalling, not in the drawing or the
SOLIDWORKS installation. Other API calls in the same session return normal
values.

## Workaround

Use a typed COM client such as C# with the SOLIDWORKS interop assembly when API
ground truth is required, or recover the display-list grammar directly. Do not
treat an empty or unindexable late-bound result as proof that the view has no
edges.

## Evidence

`OraclePolylines.vbs` and `OracleOutline.vbs` under the shared `.rescratch`
workspace produced:

```
VIEW=Drawing View1 TYPE=7
TOTAL=75
I=0 VT=0 V=

VIEW=Sheet1 TYPE=1 VT=8197 ARR=True
```

The documented view positions are still recovered from `Contents/DisplayLists`
and covered by `TestPos`. Outlines, dimensions, and annotations remain
unrecovered.
