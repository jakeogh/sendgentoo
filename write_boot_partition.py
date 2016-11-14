#!/usr/bin/env python3

import os
import sys
import time
import click
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.command import run_command
from write_gpt import write_gpt
from write_zfs_root_filesystem_on_device import write_zfs_root_filesystem_on_device
from kcl.printops import cprint

def write_boot_partition(device, force):
    cprint("creating boot partition on:", device)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        cprint("THIS WILL DESTROY ALL DATA ON:", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        cprint("Sleeping 5 seconds")
        time.sleep(5)

    partition_number = '3'
    start = "100MiB"
    end = "400MiB"

    output = run_command("parted -a optimal " + device + " --script -- mkpart primary " + start + ' ' + end)
    run_command("parted  " + device + " --script -- name " + partition_number + " rootfs")
    run_command("mkfs.ext4 " + device + partition_number)


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--force',  is_flag=True,  required=False)
def main(device, force):
    write_boot_partition(device=device, force=force)

if __name__ == '__main__':
    main()
    quit(0)

