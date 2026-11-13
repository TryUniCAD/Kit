# Some saved mesh streams keep bytes that the world does not reference

## Expectation

The `world` member references every byte of each `stream_mesh_NNN` and `Fusion_mesh_NNN` member.

## Actual behavior

Two documents in `re/Fusion/examples/.f3z/example1.f3z` hold mesh data after the last referenced span. Member numbers count the bundle documents in file-name order from 0.

| Document | Stream | Referenced bytes | Member bytes |
| --- | --- | --- | --- |
| Member 4 | `Fusion_mesh_000` | 64048 | 128096 |
| Member 7 | `stream_mesh_000` | 35460 | 91620 |
| Member 7 | `Fusion_mesh_000` | 57680 | 706104 |

The unreferenced bytes decode as vertex data, but no `world` node points to them. The native mesh serializer seeks to offset 0 before the first item of a save. The disassembly shows no call that truncates the stream.

Kit raises `ValueError("Trailing graphics mesh bytes")` for these scenes.

## Workaround

Keep the strict check. These two documents also need native class schemas that the local reflection does not hold, so Kit cannot read them yet.

## Evidence

- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [Stream coverage script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/Coverage.py)
