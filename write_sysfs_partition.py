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
#from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from write_zfs_root_filesystem_on_device import write_zfs_root_filesystem_on_device
from kcl.printops import cprint

def write_sysfs_partition(device, force, exclusive, filesystem):
    cprint("creating sysfs partition on:", device)
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

    if filesystem == 'ext4':
        if exclusive:
            #destroy_block_device_head_and_tail(device=device, force=True) #these are done in create_root_device
            #write_gpt(device)
            partition_number = '1'
            start = "0"
            end = "100%"
        else:
            partition_number = '3'
            start = "100MiB"
            end = "100%"

        output = run_command("parted " + device + " --script -- mkpart primary " + start + ' ' + end)
        if 'Error' in output:
            #cprint("Error:", output)
            quit(1)
        run_command("parted " + device + " --script -- name " + partition_number + " rootfs")
        run_command("mkfs.ext4 " + device + partition_number)

    elif filesystem == 'zfs':
        assert exclusive
        write_zfs_root_filesystem_on_device(device=device, force=True)
    else:
        cprint("unknown filesystem:", filesystem)
        quit(1)

@click.command()
@click.option('--device',     is_flag=False, required=True)
@click.option('--filesystem', is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
#@click.option('--start',     is_flag=False, required=False, type=str, default='100MiB')
#@click.option('--end',       is_flag=False, required=False, type=str, default='100%')
@click.option('--force',      is_flag=True,  required=False)
@click.option('--exclusive',  is_flag=True,  required=False)
def main(device, filesystem, force, exclusive):
    write_sysfs_partition(device=device, filesystem=filesystem, force=force, exclusive=exclusive)

if __name__ == '__main__':
    main()
    quit(0)

#set_boot_on_command = "parted " + device + " --script -- set 2 boot on"
#run_command(set_boot_on_command)
#root_partition_boot_flag_command = "parted " + device + " --script -- set 2 boot on"
#run_command(root_partition_boot_flag_command)
