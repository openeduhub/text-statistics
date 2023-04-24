#!/usr/bin/env python3
from setuptools import setup

setup(
    name="readingtime",
    version="1.0",
    description="Compute the Expected Reading Time of Text",
    author="Jonas Opitz",
    author_email="jonas.opitz@gwdg.de",
    packages=["readingtime"],
    install_requires=[
        d for d in open("requirements.txt").readlines() if not d.startswith("--")
    ],
    package_dir={"": "src"},
    entry_points={"console_scripts": ["readingtime = readingtime.main:main"]},
)
