# Paired native tree inspection

## Behavior and usage

`re/tooling/sw2026/InspectTreeParity.py` compares each frozen generated part with
its independent native source through the same operation sequence. Each lane
uses three fresh processes: open/rebuild/save, radius/depth edit/rebuild/save,
then edited fresh reopen. No view setter is imported or called.

At initial opening, rebuild, final edit and save, the observer records the
complete recursive tree and active pose. Generated nodes must equal the
corresponding source nodes in order, name, type, parent and suppression. Pose
components must match the corresponding source observation. Feature error and
warning checks, initial bodies, analytic volume/area/centre of mass, sketch
frame, fixed-centre relation and driving dimensions remain mandatory.

The source's edit trajectory is measured independently after the writer is
frozen. The observer does not assume that an original pose stays numerically
constant after editing: a native rebuild already changed one failed source
attempt's translation. Expected edited observations never enter writer input.

Every scene also requires one visible solid body through
[`IPartDoc.GetBodies2(0, True)`](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IPartDoc~GetBodies2.html).
The documented visibility filter excludes hidden bodies. This is a body-state
check, not pixel-level screenshot acceptance.

The job specifies the committed prediction receipt, public source lock, private
source-observation digest, immutable source/candidate/control paths, explicit
edit factors, observer revision and external output directory. Before private
reference access, the observer verifies the successful complete prediction
receipt, unchanged constructor identity, exact requests and output hashes, and
the public lock's private-observation digest. The first source observation is
also checked against its locked original API tree and pose.

Healthy controls bracket the whole batch. Each case requires six distinct
process-creation identities. Save operations target new external copies, and
all original source/candidate/control and private-observation hashes must remain
unchanged. The planned complete batch uses fourteen launches including controls.
No licensing process is stopped or restarted.

## Verification and limits

The new observer was inspected by AST and source only. No local tests ran.
Native execution is pending successful frozen prediction and reference-access
publication. All source and generated phases remain individually reported;
failure in either lane rejects the paired case. Vendor-saved derivatives do not
increase generated-output coverage.

This tool adds no native acceptance by itself and does not enable production
writing. Pixel viewport equality, broader feature families, arbitrary locale
selection and the complete conversion goal remain unfinished.
