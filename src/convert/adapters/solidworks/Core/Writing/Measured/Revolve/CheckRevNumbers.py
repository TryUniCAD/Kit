from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevMass import (
    ReadRevMass,
)


# the pinned native phases retain a solid and match the original mass observations to six figures
def CheckRevNumbers(Phases: dict[str, object], Opened: object, Edited: object, Reopened: object) -> None:
    for RoleName, RawValue in (
        ("open", Opened),
        ("edited", Edited),
        ("reopen", Reopened),
    ):
        Actual = ReadMeasMap(RawValue)
        Expected = ReadMeasMap(Phases.get(RoleName))
        Quantities = ReadRevMass(Actual.get("mass"))
        if (
            Actual.get("bodies") != 1
            or Expected.get("body_count") != 1
            or len(ReadMeasRows(Actual.get("features"), 32)) != Expected.get("feature_rows")
            or Actual.get("angle_radians") != Expected.get("angle_radians")
            or Actual.get("reverse") is not Expected.get("reverse")
            or Quantities != ReadRevMass(Expected.get("mass"))
            or any(
                format(Observed, ".6g") != format(Locked, ".6g")
                and (Index < 3 or max(abs(Observed), abs(Locked)) >= 1e-12)
                for Index, (Observed, Locked) in enumerate(
                    zip(
                        Quantities,
                        ReadRevMass(Expected.get("locked_source_mass")),
                        strict=True,
                    )
                )
            )
        ):
            raise ValueError("measured revolve does not match the locked native observations")
