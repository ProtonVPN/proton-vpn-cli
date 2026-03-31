#!/usr/bin/env python

from setuptools import setup, find_namespace_packages
import re

VERSIONS = 'versions.yml'
VERSION = re.search(r'version: (\S+)', open(VERSIONS, encoding='utf-8')
                    .readline()).group(1)

setup(
    name="proton-vpn-cli",
    version=VERSION,
    description="ProtonVPN CLI",
    author="Proton Technologies",
    author_email="contact@protonmail.com",
    url="https://github.com/ProtonMail/python-protonvpn-cli",
    install_requires=[
        "proton-core",
        "proton-vpn-api-core",
        "proton-keyring-linux",
        "proton-vpn-local-agent",
        "click",
        "dbus-fast",
        "tabulate"
    ],
    extras_require={
        "development": [
            "packaging",
            "pytest",
            "pytest-asyncio",
            "pytest-coverage",
            "proton-core-internal",
            "flake8",
            "pylint"
        ]
    },
    packages=find_namespace_packages(include=["proton.vpn.*"]),
    include_package_data=True,
    python_requires=">=3.9",
    license="GPLv3",
    platforms="OS Independent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Security",
    ],
    data_files=[
        ("share/bash-completion/completions", ["completions/protonvpn"]),
        ("share/zsh/site-functions", ["completions/_protonvpn"]),
        ("share/fish/vendor_completions.d", ["completions/protonvpn.fish"]),
    ],
    entry_points={
        "console_scripts": [
            ['protonvpn=proton.vpn.cli:main'],
        ],
    }
)
