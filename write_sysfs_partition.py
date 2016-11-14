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
from write_zfs_root_filesystem_on_devices import write_zfs_root_filesystem_on_devices
from kcl.printops import cprint

def write_sysfs_partition(devices, force, exclusive, filesystem, raid):
    cprint("creating sysfs partition on:", devices)
    for device in devices:
        assert not device[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    if not force:
        cprint("THIS WILL DESTROY ALL DATA ON:", devices, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        cprint("Sleeping 5 seconds")
        time.sleep(5)

    if filesystem == 'ext4':
        assert len(devices) == 1
        if exclusive:
            #destroy_block_device_head_and_tail(device=device, force=True) #these are done in create_root_device
            #write_gpt(device)
            partition_number = '1'
            start = "0%"
            end = "100%"
        else:
            partition_number = '3'
            start = "100MiB"
            end = "100%"

        output = run_command("parted -a optimal " + devices[0] + " --script -- mkpart primary " + start + ' ' + end)
        run_command("parted  " + devices[0] + " --script -- name " + partition_number + " rootfs")
        time.sleep(1)
        run_command("mkfs.ext4 " + devices[0] + partition_number)

    elif filesystem == 'zfs':
        assert exclusive
        write_zfs_root_filesystem_on_devices(devices=devices, force=True, raid=raid)
    else:
        cprint("unknown filesystem:", filesystem)
        quit(1)

@click.command()
@click.argument('devices',      required=True, nargs=-1)
@click.option('--filesystem', is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
#@click.option('--start',     is_flag=False, required=False, type=str, default='100MiB')
#@click.option('--end',       is_flag=False, required=False, type=str, default='100%')
@click.option('--force',      is_flag=True,  required=False)
@click.option('--exclusive',  is_flag=True,  required=False)
@click.option('--raid',       is_flag=False, required=True, type=click.Choice(['disk', 'mirror', 'raidz1', 'raiz2', 'raidz3', 'raidz10', 'raidz50', 'raidz60']))
def main(devices, filesystem, force, exclusive, raid):
    write_sysfs_partition(devices=devices, filesystem=filesystem, force=force, exclusive=exclusive, raid=raid)

if __name__ == '__main__':
    main()
    quit(0)

#set_boot_on_command = "parted " + device + " --script -- set 2 boot on"
#run_command(set_boot_on_command)
#root_partition_boot_flag_command = "parted " + device + " --script -- set 2 boot on"
#run_command(root_partition_boot_flag_command)

