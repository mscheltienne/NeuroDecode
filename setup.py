import os
import platform
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.develop import develop as _develop
from setuptools.dist import Distribution

_PATTERNS: dict[str, str] = {
    "Linux": "liblsl*.so*",
    "Darwin": "liblsl*.dylib",
    "Windows": "lsl*.dll",
}


class BinaryDistribution(Distribution):  # noqa: D101
    def has_ext_modules(self):  # noqa: D102
        return True


class build_ext(_build_ext):  # noqa: D101
    def run(self):
        """Build 'liblsl' with cmake as part of the extension build process."""
        skip = os.environ.get("MNE_LSL_SKIP_LIBLSL_BUILD", False)
        if skip:
            print("Skipping build of liblsl.")  # noqa: T201
            return
        src = Path(__file__).parent / "src" / "liblsl"
        assert src.exists()  # sanity-check
        with TemporaryDirectory() as build_dir:
            args = [
                "cmake",
                "-S",
                str(src),
                "-B",
                build_dir,
                "-DCMAKE_BUILD_TYPE=Release",
            ]
            if platform.system() == "Darwin":
                args.append("-DCMAKE_OSX_DEPLOYMENT_TARGET=11")
            subprocess.run(args, check=True)
            subprocess.run(
                ["cmake", "--build", build_dir, "--config", "Release"], check=True
            )
            # locate the build files and move them to mne_lsl.lsl.lib
            if platform.system() == "Windows":
                build_dir = Path(build_dir) / "Release"
            else:
                build_dir = Path(build_dir)
            lib_files = [
                elt
                for elt in build_dir.glob(_PATTERNS[platform.system()])
                if not elt.is_symlink()
            ]
            assert len(lib_files) == 1  # sanity-check
            dst = (
                Path(__file__).parent / "src" / "mne_lsl" / "lsl" / "lib"
                if self.inplace
                else Path(self.build_lib) / "mne_lsl" / "lsl" / "lib"
            )
            dst.mkdir(parents=True, exist_ok=True)
            print(f"Moving {lib_files[0]} to {dst / lib_files[0].name}")  # noqa: T201
            shutil.move(lib_files[0], dst / lib_files[0].name)
        super().run()


class develop(_develop):  # noqa: D101
    def run(self):  # noqa: D102
        self.run_command("build_ext")
        super().run()


class bdist_wheel_abi3(bdist_wheel):  # noqa: D101
    def get_tag(self):  # noqa: D102
        python, abi, plat = super().get_tag()
        if python.startswith("cp"):
            return "cp310", "abi3", plat
        return python, abi, plat


setup(
    cmdclass={
        "build_ext": build_ext,
        "bdist_wheel": bdist_wheel_abi3,
        "develop": develop,
    },
    distclass=BinaryDistribution,
)
