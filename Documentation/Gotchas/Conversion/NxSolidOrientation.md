# A solid with the wrong loop winding measures zero in NX

## Expectation

A closed, correctly oriented box encodes to a Parasolid stream that NX can
measure, because every geometric check passes: the loops close, every loop vertex
lies on its surface, the shell is closed and the region is solid.

## Observed behavior

NX 2506 opens the part, lists one body, reports `IsSolidBody` true, and returns
`VOLUME 0.0`, `AREA 0.0`, `MASS 0.0`. It also enumerates all six faces and twelve
edges, so the topology parsed fine.

Two independent causes were measured:

- NX's own bodies wind every face loop **against** the face's surface normal
  (`loop normal . surface normal = -1`), while `BuildPrism` winds with it
  (`+1`). Wind the loops the other way and the body measures correctly.
- `parasolid.first_fin` is not optional. NX names the coedge whose `reversed`
  flag is `False`; without the attribute the encoder started at
  `edge_coedges[edge][0]`, which is the reversed fin about half the time, and NX
  bound one face instead of six.

Reversing a loop by reversing its coedge list alone is not a valid flip: the
chain becomes disconnected and the encoder refuses it with
`B-rep loop ... is disconnected or open`. The list must be reversed and every
coedge's `reversed` flag flipped together.

## Workaround

Encode through `EncodeBrepModel`, which now performs both fixes. When building a
model by hand, wind each face's outer loop against its surface normal and give
each edge a `parasolid.first_fin` pointing at the coedge with `reversed=False`.

## Evidence

```text
authored 60x30x20 box before the fix   BODIES 1, VOLUME 0.0
same box, loops wound against normals
  and first_fin set                   BODIES 1, VOLUME 36000.0, MASS 0.28190304
decoded NX body re-encoded             BODIES 1, VOLUME 23999.999999999996
```

Attribute stripping showed the contract is narrow: removing the rank layer, the
senses, `carrier_record` or `vertex_fins` still measures `24000`, and only
`first_fin` changes the result.
