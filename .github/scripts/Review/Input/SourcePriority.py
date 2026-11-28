# bounded partial reviews must inspect code before large generated views consume the source budget
def SourcePriority(Entry: dict[str, object]) -> tuple[bool, bool, str]:
    FileName = str(Entry["filename"])
    return (
        FileName.startswith("Documentation/Planning/Generated/"),
        not FileName.lower().endswith(
            (
                ".py",
                ".cjs",
                ".mjs",
                ".js",
                ".ts",
                ".tsx",
                ".cs",
                ".java",
                ".kt",
                ".yml",
                ".yaml",
                ".toml",
                ".json",
            )
        ),
        FileName,
    )
