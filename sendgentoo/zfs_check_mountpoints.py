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
from asserttool import eprint
from asserttool import ic
from asserttool import maxone


@click.command()
@click.option('--verbose', is_flag=True,)
@click.option('--debug', is_flag=True,)
@click.pass_context
def zfs_check_mountpoints(ctx,
                          *,
                          verbose: bool,
                          debug: bool,
                          ):

    mountpoints = sh.zfs.get('mountpoint')
    ic(mountpoints)

    for line in mountpoints.splitlines():
        line = ' '.join(line.split())
        ic(line)
        #mountpoint =
