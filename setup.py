#!/usr/bin/env python3
from setuptools import setup

setup(
    name="readingspeed",
    version="1.0",
    description="Compute the Expected Reading Time of Text",
    author="Jonas Opitz",
    author_email="jonas.opitz@gwdg.de",
    packages=["readingspeed"],
    install_requires=[
        d for d in open("requirements.txt").readlines() if not d.startswith("--")
    ],
    package_dir={"": "src"},
    entry_points={"console_scripts": ["readingspeed = readingspeed.main:main"]},
)
