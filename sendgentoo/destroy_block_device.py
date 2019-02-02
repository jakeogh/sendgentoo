#!/usr/bin/env python3

import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from kcl.deviceops import warn
from kcl.command import run_command

def destroy_block_device_ask(device, force, source):
    assert isinstance(force, bool)
    assert source in ['urandom', 'zero']
    assert not device[-1].isdigit()
    eprint("destroying device:", device)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        warn((device,))
    wipe_command = "dd if=/dev/" + source + " of=" + device
    print(wipe_command)
    run_command(wipe_command, verbose=True, expected_exit_code=1)  # dd returns 1 when it hits the end of the device



@click.command()
@click.argument('device', required=True, nargs=1)
@click.option('--force', is_flag=True, required=False)
@click.option('--source', is_flag=False, required=False, type=click.Choice(['urandom', 'zero']), default="urandom")
def destroy_block_device(device, force, source):
    destroy_block_device_ask(device=device, force=force, source=source)
