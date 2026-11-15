# Drawing orientation is derived from the model view name

## Expectation

The orientation matrix in `Contents/Definition` is authoritative, so rewriting
it changes the view orientation.

## Actual behavior

Rewriting the nine-double matrix and the direction vector leaves the view
orientation unchanged. `View.GetViewXform` still returns the original rotation.

The authoritative orientation is the UTF-16 model view name stored in
`Contents/Definition`:

```
*Front
*Top
*Right
*Isometric
```

Rewriting that name in place also fails: replacing `*Top` with `*Right` makes
`OpenDoc` return null, because the name is referenced by the model view record
and the reference is not a plain string.

## Workaround

Treat the orientation as read-only. `WriteDrawing` rewrites only the position
and scale records. Changing the orientation requires regenerating the model view
record and its reference, which is not recovered.

## Evidence

`ident-top.SLDDRW` rewrote the top view matrix to identity and kept flag `1`;
`View.GetViewXform` still returned the top rotation. `rightname-top.SLDDRW`
replaced `*Top` with `*Right`; `OpenDoc` returned null.

`written-front.SLDDRW` and `written-standard.SLDDRW` changed only position and
scale, and SOLIDWORKS reported the new values through `View.GetXform`.
