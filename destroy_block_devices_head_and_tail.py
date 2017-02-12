#!/usr/bin/env python3
import os
import click
import time
import subprocess
import sys
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.fileops import get_file_size
from backup_byte_range import backup_byte_range
from kcl.printops import cprint
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail

def destroy_block_devices_head_and_tail(devices, size, note, force, no_backup):
    for device in devices:
        assert isinstance(no_backup, bool)
        assert not device[-1].isdigit()
        cprint("destroying device:", device)
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    if not force:
        cprint("THIS WILL DESTROY ALL DATA ON ", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        cprint("Sleeping 5 seconds")
        time.sleep(5)

    for device in devices:
        destroy_block_device_head_and_tail(device, size, note, force, no_backup)

@click.command()
@click.argument('devices', required=True, nargs=-1)
@click.option('--size',   is_flag=False, required=False, type=int, default=(1024*1024*128))
@click.option('--note',   is_flag=False, required=False)
@click.option('--force',  is_flag=True,  required=False)
@click.option('--no-backup', is_flag=True,  required=False)
def main(devices, size, note, force, no_backup):
    destroy_block_device_head_and_tail(devices, size, note, force, no_backup)

if __name__ == '__main__':
    main()
    quit(0)

