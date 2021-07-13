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


import click
import sh
from asserttool import eprint
from asserttool import ic
from run_command import run_command
from timetool import get_timestamp


@click.command()
@click.argument('path', required=True, nargs=1)
@click.option('--simulate', is_flag=True,)
@click.option('--verbose', type=str,)
@click.option('--debug', type=str,)
@click.pass_context
def create_zfs_filesystem_snapshot(ctx,
                                   path: str,
                                   simulate: bool,
                                   verbose: bool,
                                   debug: bool,
                                   ) -> None:

    if verbose:
        ic()

    assert not path.startswith('/')
    assert len(path.split()) == 1
    assert len(path) > 3

    timestamp = str(int(float(get_timestamp())))
    snapshot_path = path + "@__{timestamp}__".format(timestamp=timestamp)
    command = sh.zfs.snapshot.bake(snapshot_path)

    if verbose or simulate:
        ic(command)

    if not simulate:
        #run_command(command, verbose=True, expected_exit_status=0)
        command()
