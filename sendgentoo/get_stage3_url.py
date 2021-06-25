#!/usr/bin/env python3
# flake8: noqa           # flake8 has no per file settings :(
# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=C0114  #      Missing module docstring (missing-module-docstring)
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

import click
from nettool import construct_proxy_dict
from nettool import download_file


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
    from icecream import icr  # https://github.com/jakeogh/icecream
except ImportError:
    ic = eprint
    icr = eprint


def get_stage3_url(stdlib: str,
                   multilib: bool,
                   arch: str,
                   proxy_dict: dict,
                   ):
    #mirror = 'http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/'
    mirror = 'http://gentoo.osuosl.org/releases/' + arch + '/autobuilds/'
    if stdlib == 'glibc':
        if not multilib:
            latest = 'latest-stage3-' + arch + '-hardened+nomultilib.txt'
        else:
            latest = 'latest-stage3-' + arch + '-hardened.txt'
    if stdlib == 'musl':
        latest = ''
        eprint("cant use musl yet")
        quit(1)
    if stdlib == 'uclibc':
        latest = 'latest-stage3-' + arch + '-uclibc-hardened.txt'
        eprint("uclibc wont compile efivars")
        quit(1)
    get_url = mirror + latest
    text = download_file(url=get_url, proxy_dict=proxy_dict)
    #r = requests.get(mirror + latest)
    eprint(text)
    autobuild_file_lines = text.split('\n')
    #r.close()
    path = ''
    for line in autobuild_file_lines:
        if 'stage3-' + arch in line:
            path = line.split(' ')[0]
            break
    #eprint('path:', path)
    assert 'stage3' in path
    url = mirror + path
    #eprint("url:", url)
    return url


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']),)
@click.option('--multilib', is_flag=True,)
@click.option('--arch', is_flag=False, required=True, type=click.Choice(['amd64']))
@click.option('--proxy', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
def main(stdlib: str,
         multilib: bool,
         arch: str,
         proxy: bool,
         verbose: bool,
         debug: bool,
         ):
    if proxy:
        proxy_dict = construct_proxy_dict(verbose=verbose, debug=debug,)
    url = get_stage3_url(stdlib=stdlib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
    eprint(url)
