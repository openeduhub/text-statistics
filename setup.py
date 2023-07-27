#!/usr/bin/env python3
from setuptools import setup

setup(
    name="text-statistics",
    version="1.0.4",
    description="Compute various statistics on text, like readability or reading time",
    author="Jonas Opitz",
    author_email="jonas.opitz@gwdg.de",
    packages=["text_statistics"],
    install_requires=[
        d for d in open("requirements.txt").readlines() if not d.startswith("--")
    ],
    package_dir={"": "src"},
    entry_points={"console_scripts": ["webservice = text_statistics.webservice:main"]},
)
