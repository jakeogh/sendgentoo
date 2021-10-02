#!/usr/bin/env python3

# flake8: noqa           # flake8 has no per file settings :(
# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement
# pylint: disable=C0305  # Trailing newlines editor should fix automatically, pointless warning


import sys
from pathlib import Path
from typing import Optional

import click
from asserttool import eprint
from asserttool import ic
from nettool import construct_proxy_dict
from nettool import download_file

#from retry_on_exception import retry_on_exception
from .get_stage3_url import get_stage3_url


def download_stage3(*,
                    destination_dir: Path,
                    stdlib: str,
                    multilib: bool,
                    arch: str,
                    proxy_dict: dict,
                    ):
    destination_dir = Path(destination_dir)
    url = get_stage3_url(proxy_dict=proxy_dict, stdlib=stdlib, multilib=multilib, arch=arch)
    ic(url)
    stage3_file = download_file(url=url, destination_dir=destination_dir, proxy_dict=proxy_dict)
    download_file(url=url + '.CONTENTS', destination_dir=destination_dir, proxy_dict=proxy_dict)
    download_file(url=url + '.DIGESTS', destination_dir=destination_dir, proxy_dict=proxy_dict)
    download_file(url=url + '.DIGESTS.asc', destination_dir=destination_dir, proxy_dict=proxy_dict)
    return Path(stage3_file)


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--arch', is_flag=False, required=True, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']))
@click.option('--multilib', is_flag=True, required=False)
@click.option('--proxy', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
def main(stdlib: str,
        arch: str,
        multilib: bool,
        proxy: str,
        verbose: bool,
        debug: bool,
        ):
    if proxy:
        proxy_dict = construct_proxy_dict(verbose=verbose, debug=debug,)
    destination_dir = Path('/var/db/repos/gentoo/distfiles/')
    download_stage3(destination_dir=destination_dir,
                    stdlib=stdlib,
                    multilib=multilib,
                    arch=arch,
                    proxy_dict=proxy_dict,)
