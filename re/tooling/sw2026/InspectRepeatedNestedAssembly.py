from __future__ import annotations

from InspectGeneratedNestedAssembly import TrialProfile, main


PROFILE = TrialProfile(
    name="GeneratedRepeatedNestedAssembly01",
    script="InspectRepeatedNestedAssembly.py",
    schema="kit.sw2026.generated-repeated-nested-assembly-native-trial.v1",
    evidence_file="GeneratedRepeatedNestedAssemblyBundle01.json",
    evidence_sha256="168c45f25116ce4089d7830fe463f0d1becc3aa18768eb3d2297683fae4df6ec",
    control="N02MixedRepeated",
)


if __name__ == "__main__":
    raise SystemExit(main(PROFILE))
