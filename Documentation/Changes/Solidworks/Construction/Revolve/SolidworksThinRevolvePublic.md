# Qualified thin revolve model writing and cold readback

The SOLIDWORKS SDK writes a forward partial open-line thin boss from the
portable angular and wall drivers on a canonical principal frame. The cold
reader retains the sketch and actual centreline selection, independent active
drivers and generating body. It also derives a single analytic solid when the
caller requests B-rep. Other support orientation, stored body state and
unrepresented feature history remain outside this profile.

Four independently locked native sources passed the complete edit, save and
reopen lifecycle in 18 SOLIDWORKS 2026 SP05.2 processes. The separately frozen
SDK packet compares normal registry, direct, file and stream output and strict
generated readback against those exact native-tested model-only inputs. It
reproduces all four files, verifies 24 public output paths and 16 strict
readbacks and preserves zero runtime input reads. Nine unqualified requests
refuse before publication.
[Scope and verification](../../../../../re/solidworks/records/ThinRevolvePublic2026.md) ·
[Public receipt](../../../../../re/solidworks/measurements/2026/SdkThinRevolvePublicParity01.json)
