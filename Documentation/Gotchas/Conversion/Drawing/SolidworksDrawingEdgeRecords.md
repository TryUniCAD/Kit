# Drawing edge records are not the stream geometry

## Expectation

`View.GetPolylines5` returns the same coordinates that are stored in
`Contents/DisplayLists` or `Contents/VBLists`, so the stream can be segmented by
the API record shape.

## Actual behavior

The typed C# dumper returns a flat double array. Each visible edge uses 15
doubles:

```
0,0,0,0,-1,1,-1,0,2, x1,y1,z1,x2,y2,z2
```

The first nine values are a constant header. The final six are two view-local
three-dimensional points. A five-edge view therefore returns 75 doubles.

Those view-local coordinates do not appear as doubles in the drawing streams.
`Contents/DisplayLists` and `Contents/VBLists` instead contain runs of
model-space values such as `0.0185,0.016,0.0045,0.042,0.032,0.009`, and no
recovered record count or delimiter separates them into edges. Searching for
the API points (`0.0005`, `-0.0235`, and so on) finds nothing.

## Workaround

Use the API grammar to validate an eventual stream decoder, but do not assume
the API points are stored verbatim. Recovering the stream requires the model
coordinate records plus the view transform, neither of which is decoded yet.
Keep drawing edge parsing out of production until that mapping is proven.

## Evidence

`re/tooling/harness/OraclePolylines.cs` compiled with the Windows .NET Framework
and produced:

```
VIEW=Drawing View1 TYPE=7
DOUBLES=75
0,0,0,0,-1,1,-1,0,2,0.0005,0.016,0.0045,-0.0235,-0.002,0.0045,...
```

The same run gave 105 doubles for a seven-edge view and 180 for a twelve-edge
view, exactly 15 per edge.
