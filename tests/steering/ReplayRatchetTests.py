from __future__ import annotations

import os as OsLib
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[2]

KAssertions = Unittest.TestCase()

KTableText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
)
"""

KGrownText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
    (12, 2, 3, "classref", 41),
)
"""

KProgramText = "EncodedData = ReplayResolved((), 0)\n"

KBalancedText = "src/family\tREP001\t2\nsrc/family\tREP002\t1\n"


def WriteTree(FolderPath: FilePath, TableText: str, BaselineText: str) -> None:
    MethodPath = FolderPath / "src" / "family" / "Methods" / "Table.py"
    MethodPath.parent.mkdir(parents=True)
    _ = MethodPath.write_text(TableText, encoding="utf-8")
    ProgramPath = FolderPath / "src" / "family" / "Program.py"
    _ = ProgramPath.write_text(KProgramText, encoding="utf-8")
    BaselinePath = FolderPath / "Baseline.txt"
    _ = BaselinePath.write_text(BaselineText, encoding="utf-8")


def RunRatchet(
    FolderPath: FilePath, *ExtraArgs: str
) -> Subprocess.CompletedProcess[str]:
    EnvValues = {**OsLib.environ, "PYTHONPATH": str(KRepoRoot)}
    return Subprocess.run(
        [
            System.executable,
            "-m",
            "tools.Donors.CheckReplays",
            "--baseline-file",
            "Baseline.txt",
            *ExtraArgs,
            "src",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=FolderPath,
        env=EnvValues,
    )


class TestBalanced(Unittest.TestCase):

    @staticmethod
    def CheckBalanced() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, KBalancedText)
            ResultInfo = RunRatchet(FolderPath)
        CaseSelf.assertEqual(
            ResultInfo.returncode, 0, ResultInfo.stdout + ResultInfo.stderr
        )
        CaseSelf.assertIn("2 recorded field operations", ResultInfo.stdout)


class TestGrowth(Unittest.TestCase):

    @staticmethod
    def CheckGrowth() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KGrownText, KBalancedText)
            ResultInfo = RunRatchet(FolderPath)
            UpdateInfo = RunRatchet(FolderPath, "--update-baseline")
            BaselineText = (FolderPath / "Baseline.txt").read_text(encoding="utf-8")
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("grew from 2 to 3", ResultInfo.stdout)
        CaseSelf.assertEqual(UpdateInfo.returncode, 1)
        CaseSelf.assertEqual(BaselineText, KBalancedText)


class TestNewRoot(Unittest.TestCase):

    @staticmethod
    def CheckNewRoot() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, KBalancedText)
            OtherPath = FolderPath / "src" / "other" / "Methods" / "Table.py"
            OtherPath.parent.mkdir(parents=True)
            _ = OtherPath.write_text(KTableText, encoding="utf-8")
            ResultInfo = RunRatchet(FolderPath)
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("src/other: REP001", ResultInfo.stdout)
        CaseSelf.assertIn("are new (2)", ResultInfo.stdout)


class TestShrink(Unittest.TestCase):

    @staticmethod
    def CheckShrink() -> None:
        CaseSelf = KAssertions
        LooseText = KBalancedText.replace("REP001\t2", "REP001\t5")
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, LooseText)
            ResultInfo = RunRatchet(FolderPath)
            UpdateInfo = RunRatchet(FolderPath, "--update-baseline")
            FinalInfo = RunRatchet(FolderPath)
            BaselineText = (FolderPath / "Baseline.txt").read_text(encoding="utf-8")
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("fell from 5 to 2", ResultInfo.stdout)
        CaseSelf.assertEqual(UpdateInfo.returncode, 0, UpdateInfo.stderr)
        CaseSelf.assertEqual(FinalInfo.returncode, 0, FinalInfo.stderr)
        CaseSelf.assertTrue(BaselineText.endswith(KBalancedText))


class TestInputs(Unittest.TestCase):

    @staticmethod
    def CheckInputs() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, "src/family\tREP001\n")
            MalformedInfo = RunRatchet(FolderPath)
            (FolderPath / "Baseline.txt").unlink()
            MissingInfo = RunRatchet(FolderPath)
        CaseSelf.assertEqual(MalformedInfo.returncode, 2)
        CaseSelf.assertEqual(MissingInfo.returncode, 2)
