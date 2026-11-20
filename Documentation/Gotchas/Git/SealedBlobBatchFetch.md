# Sealed blob batch fetch

A public source repository can serve its pinned branch and individual objects
while a runner's batch fetch of explicit blob IDs exits unsuccessfully. This
stopped a [Linux test shard](https://github.com/TryUniCAD/Kit/actions/runs/44741548782/job/136306861581)
before pytest started.

Use the path from the sealed tree and its exact revision to retrieve a refused
object, then verify its Git blob ID before writing it into the object database.
Keep the final inventory and historical tree checks enabled.
