#!/usr/bin/env python3

import click
from kcl.commandops import run_command
from kcl.printops import eprint

@click.command()
@click.argument('pool', required=True, nargs=1)
@click.argument('name', required=True, nargs=1)
@click.option('--simulate', is_flag=True, required=False)
@click.option('--encrypt', is_flag=True, required=False)
@click.option('--nfs', is_flag=True, required=False)
#@click.option('--force', is_flag=True, required=False)
@click.option('--exec', 'exe', is_flag=True, required=False)
@click.option('--nomount', is_flag=True, required=False)
@click.option('--reservation', type=str, required=False)
def create_zfs_filesystem(pool, name, simulate, encrypt, nfs, exe, nomount, reservation):
    eprint("make_zfs_filesystem_on_devices()")

    assert not pool.startswith('/')
    assert not name.startswith('/')
    assert len(pool.split()) == 1
    assert len(name.split()) == 1
    assert len(name) > 2

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    #run_command("modprobe zfs || exit 1")

    command = "zfs create"
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

    print(command)
    if not simulate:
        run_command(command, verbose=True, expected_exit_code=0)

