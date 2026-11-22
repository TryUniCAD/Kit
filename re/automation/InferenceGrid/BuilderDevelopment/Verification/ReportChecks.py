# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose, isfinite


# structured mismatches preserve independent acceptance diagnostics for bounded repairs
class ReportChecks:
    def __init__(self, Expectations):
        self.Expectations = Expectations if isinstance(Expectations, dict) else {}
        self.Diagnostics = []

    def Add(self, Path, Expected, Actual, Classification="builder_defect"):
        self.Diagnostics.append(
            {
                "path": Path,
                "expected": Expected,
                "actual": Actual,
                "classification": Classification,
            }
        )

    def Field(self, Value, Name, Path, Classification="verifier_support_missing"):
        if not isinstance(Value, dict) or Name not in Value:
            self.Add(Path + "." + Name, "collected field", "missing", Classification)
            return None
        return Value[Name]

    def Equal(self, Actual, Expected, Path, Classification="builder_defect"):
        if (
            Actual is None
            and Expected is not None
            and Classification == "builder_defect"
        ):
            Classification = "verifier_support_missing"
        if type(Expected) is bool:
            Same = Actual is Expected
        else:
            Same = Actual == Expected and not (
                type(Actual) is bool and type(Expected) in (int, float)
            )
        if not Same:
            self.Add(Path, Expected, Actual, Classification)

    def Near(
        self,
        Actual,
        Expected,
        Path,
        Tolerance="linear_mm",
        Classification="builder_defect",
    ):
        if Actual is None and Classification == "builder_defect":
            Classification = "verifier_support_missing"
        if (
            type(Actual) not in (int, float)
            or not isfinite(Actual)
            or not isclose(
                Actual,
                Expected,
                rel_tol=self.Expectations["tolerances"]["relative"],
                abs_tol=self.Expectations["tolerances"][Tolerance],
            )
        ):
            self.Add(Path, Expected, Actual, Classification)

    def Vector(
        self,
        Actual,
        Expected,
        Path,
        Tolerance="linear_mm",
        Classification="builder_defect",
    ):
        if Actual is None and Classification == "builder_defect":
            Classification = "verifier_support_missing"
        if not isinstance(Actual, list) or len(Actual) != len(Expected):
            self.Add(Path, Expected, Actual, Classification)
            return
        for Index, (Found, Target) in enumerate(zip(Actual, Expected, strict=True)):
            self.Near(Found, Target, f"{Path}[{Index}]", Tolerance, Classification)

    def Result(self):
        Priority = (
            "license_unavailable",
            "application_unavailable",
            "unhealthy_session",
            "source_mismatch",
            "builder_defect",
            "verifier_support_missing",
        )
        Kinds = {Item["classification"] for Item in self.Diagnostics}
        Classification = next((Kind for Kind in Priority if Kind in Kinds), "verified")
        return {
            "verified": not self.Diagnostics,
            "classification": Classification,
            "diagnostics": self.Diagnostics,
            "expectations_sha256": self.Expectations.get("expectations_sha256"),
            "feature": self.Expectations.get("feature"),
            "conversion_qualified": False,
        }
