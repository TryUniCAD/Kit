# varied neutral requests exercise long unicode independent masks and both derived document tails
def DefSettingsCases() -> list[dict[str, object]]:
    Cases: list[dict[str, object]] = []
    for Index, (Kind, Standard, NameValue) in enumerate(
        (
            ("part", "moISO_c", "Geometric β"),
            ("part", "moJIS_c", "設計 🚲 " + "K" * 262),
            ("assembly", "moDIN_c", "Assembly δ"),
            ("assembly", "moGB_c", "上部 journal"),
        )
    ):
        Cases.append(
            {
                "mode": "build",
                "kind": Kind,
                "version": 19000,
                "presentation": {
                    "drafting_standard": Standard,
                    "detail_flags": [Index, 30 + Index, 47, 63],
                    "tessellation": [
                        13 + Index,
                        32 - Index,
                        47 * Index,
                        bool(Index % 2),
                    ],
                    "journal_name": NameValue,
                    "system_preference_7a": bool(Index % 2),
                },
                "density_kg_m3": 4123.75 + 357.5 * Index,
                "save_as_part_preferences": {
                    "5fc": True,
                    "5fd": -0.4 if Index == 2 else 1.7,
                    "5fe": False,
                    "5ff": 1.25,
                    "600": True,
                    "601": False,
                    "602": True,
                    "603": False,
                    "604": True,
                    "605": -9 - Index,
                },
            }
        )
    return Cases
