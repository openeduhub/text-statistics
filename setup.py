#!/usr/bin/env python3
from setuptools import setup
from src.text_statistics._version import __version__

setup(
    name="text-statistics",
    version=__version__,
    description="Compute various statistics on text, like readability or reading time",
    author="Jonas Opitz",
    author_email="jonas.opitz@gwdg.de",
    packages=["text_statistics"],
    install_requires=[
        d for d in open("requirements.txt").readlines() if not d.startswith("--")
    ],
    package_dir={"": "src"},
    entry_points={
        "console_scripts": ["text-statistics = text_statistics.webservice:main"]
    },
)
