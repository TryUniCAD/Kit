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

`Contents/VBLists` stores model-space edges, not the view-local API points. Each
view section is delimited by a UTF-16 `model@Drawing ViewN` string. The first
count of at least two before the next view name selects a block; edges start 20
bytes after that count and repeat every 204 bytes as six doubles: start XYZ and
end XYZ. Require every parsed view to have a block and reject the drawing when
one is missing. Do not assume the API points are stored verbatim.

## Evidence

`re/tooling/harness/OraclePolylines.cs` compiled with the Windows .NET Framework
and produced:

```
VIEW=Drawing View1 TYPE=7
DOUBLES=75
0,0,0,0,-1,1,-1,0,2,0.0005,0.016,0.0045,-0.0235,-0.002,0.0045,...
```

The same run gave 105 doubles for a seven-edge view and 180 for a twelve-edge
view, exactly 15 per edge. The stream blocks recover the same counts: 5, 7, 7,
and 12 for the four standard views, and 5, 7, and 10 for the angled views.
