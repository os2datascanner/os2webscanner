#!/usr/bin/env python3

import pathlib

import setuptools

setuptools.setup(
    install_requires=(
        pathlib.Path(__file__)
        .parent.joinpath("doc", "requirements.txt")
        .read_text()
        .splitlines()
    )
)
