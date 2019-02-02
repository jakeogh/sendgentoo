#!/usr/bin/env python3

import click
import time
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from kcl.command import run_command
from .destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from kcl.deviceops import warn


def write_mbr(device, no_wipe, force, no_backup):
    eprint("writing MBR to:", device)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        warn((device,))
    if not no_wipe:
        destroy_block_device_head_and_tail(device=device, force=force, no_backup=no_backup)
        #run_command("sgdisk --zap-all " + boot_device)

    run_command("parted " + device + " --script -- mklabel msdos")
    #run_command("parted " + device + " --script -- mklabel gpt")
    #run_command("sgdisk --clear " + device) #alt way to greate gpt label

@click.command()
@click.option('--device',     is_flag=False, required=True)
#@click.option('--device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--force',      is_flag=True,  required=False)
@click.option('--no-wipe',    is_flag=True,  required=False)
@click.option('--no-backup',  is_flag=True,  required=False)
def main(device, force, no_wipe, no_backup):
    write_mbr(device=device, force=force, no_wipe=no_wipe, no_backup=no_backup)


if __name__ == '__main__':
    main()
