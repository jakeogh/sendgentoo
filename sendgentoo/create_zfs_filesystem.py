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
from icecream import ic
from run_command import run_command
from kcl.printops import eprint

@click.command()
@click.argument('pool', required=True, nargs=1)
@click.argument('name', required=True, nargs=1)
@click.option('--simulate', is_flag=True, required=False)
@click.option('--encrypt', is_flag=True, required=False)
@click.option('--nfs', is_flag=True, required=False)
@click.option('--exec', 'exe', is_flag=True, required=False)
@click.option('--nomount', is_flag=True, required=False)
@click.option('--reservation', type=str, required=False)
@click.option('--verbose', type=str, required=False)
def create_zfs_filesystem(pool,
                          name,
                          simulate,
                          encrypt,
                          nfs,
                          exe,
                          nomount,
                          verbose,
                          reservation):

    if verbose:
        ic()

    assert not pool.startswith('/')
    assert not name.startswith('/')
    assert len(pool.split()) == 1
    assert len(name.split()) == 1
    assert len(name) > 2

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    #run_command("modprobe zfs || exit 1")

    command = "zfs create -o setuid=off -o devices=off"
    if encrypt:
        command += " -o encryption=aes-256-gcm"
        command += " -o keyformat=passphrase"
        command += " -o keylocation=prompt"
    if nfs:
        command += " -o sharenfs=on"
    if not exe:
        command += " -o exec=off"
    if reservation:
        command += " -o reservation=" + reservation

    if not nomount:
        command += " -o mountpoint=/" + pool + '/' + name

    command += ' ' + pool + '/' + name

    if verbose or simulate:
        ic(command)

    if not simulate:
        run_command(command, verbose=True, expected_exit_status=0)

