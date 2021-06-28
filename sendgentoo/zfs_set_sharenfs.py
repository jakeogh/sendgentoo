#!/usr/bin/env python3

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

import sys

import click
import sh
#from run_command import run_command
from asserttool import maxone


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


@click.command()
@click.argument('filesystem', required=True, nargs=1)
@click.argument('subnet', required=True, nargs=1)
@click.option('--no-root-write', is_flag=True,)
@click.option('--off', is_flag=True,)
@click.option('--verbose', is_flag=True,)
@click.option('--debug', is_flag=True,)
def zfs_set_sharenfs(filesystem: str,
                     subnet: str,
                     off: bool,
                     no_root_write: bool,
                     verbose: bool,
                     debug: bool,
                     ):


    maxone([off, no_root_write])

    assert not filesystem.startswith('/')
    assert len(filesystem.split()) == 1
    assert len(filesystem.split()) == 1
    assert len(filesystem) > 2

    if verbose:
        eprint(sh.zfs.get('sharenfs', filesystem))

    if off:
        sh.zfs.set('sharenfs=off')
        return

    sharenfs_list =  ['sync', 'wdelay', 'hide', 'crossmnt', 'secure', 'no_all_squash', 'no_subtree_check', 'secure_locks', 'mountpoint', 'anonuid=65534', 'anongid=65534', 'sec=sys']
    # these cause zfs set sharenfs= command to fail:
    # ['acl', 'no_pnfs']

    sharenfs_list.append('rw=' + subnet)

    if no_root_write:
        sharenfs_list.append('root_squash')
    else:
        sharenfs_list.append('no_root_squash')

    sharenfs_line = ','.join(sharenfs_list)
    if verbose:
        ic(sharenfs_line)

    #sharenfs_line = 'sharenfs=*(' + sharenfs_line + ')'
    sharenfs_line = 'sharenfs=' + sharenfs_line
    if verbose:
        ic(sharenfs_line)

    zfs_command = sh.zfs.set.bake(sharenfs_line)
    print(zfs_command(filesystem))
