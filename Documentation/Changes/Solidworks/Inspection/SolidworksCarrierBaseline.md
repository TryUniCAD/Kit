# SOLIDWORKS analytic carrier baseline

The offline integration tests read committed native parts. They check plane
normals and support offsets, line endpoints, and face and edge counts against
the solidworks-059 ground truth. The variation changes the box height. The
P05 outer-radius edit checks the cylinder and circle radii and axes against
the saved measurements. The P02 control contains a sketch only and supplies no
body carriers.

The reader already exposes lines, planes, circles, and cylinders as analytic
geometry. These tests do not change the decoder. The receipt reports the raw
carrier record separately from its typed geometry. In particular, geometry
measurements do not establish the meaning of every header field. The original
payload also contains more than the analytic records.

Replaying the successful SOLIDWORKS inputs listed in the placement campaign
through the research reader and receipt evidence collector gave this result
both before and after the test change:

```text
Counter({'/brep/curves/*/attributes/carrier_record': 1332, '/brep/surfaces/*/attributes/carrier_record': 666, '/brep_payloads/*/data': 333, 'decoded': 111})
```

No retained bytes or receipt entries were removed. The next decoder change
needs loader evidence for the unclassified carrier header fields and a byte
inventory for each payload. This baseline does not establish native writer
acceptance.
