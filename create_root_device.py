#!/usr/bin/env python3

import os
import sys
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.command import run_command
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from write_gpt import write_gpt
from write_sysfs_partition import write_sysfs_partition
from kcl.printops import cprint

def create_root_device(device, partition_table, filesystem, force, exclusive):
    assert not device[-1].isdigit()
    cprint("installing gentoo on root device:", device, '(' + partition_table + ')', '(' + filesystem + ')')
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    if not force:
        cprint("THIS WILL DESTROY ALL DATA ON", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        cprint("Sleeping 5 seconds")
        time.sleep(5)

    if exclusive:
        destroy_block_device_head_and_tail(device=device, force=True)
        write_gpt(device, no_wipe=True, force=force, no_backup=False)
        cprint("making exclusive root device:", device)
        start = '0'
        end = '100%'
    else:
        cprint("making 3rd partition root device:", device)
        start = '100MiB'
        end = '100%'

    write_sysfs_partition(device=device, force=True, exclusive=exclusive, filesystem=filesystem)


@click.command()
@click.option('--device',          is_flag=False, required=True)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force',           is_flag=True,  required=False)
@click.option('--exclusive',       is_flag=True,  required=False)
def main(device, partition_table, filesystem, force, exclusive):
    create_root_device(device=device, partition_table=partition_table, filesystem=filesystem, force=force, exclusive=exclusive)

if __name__ == '__main__':
    main()
    quit(0)

#boot_partition_command = "parted " + boot_device + " --script -- mkpart primary 200MiB 331MiB"
#run_command(boot_partition_command)
#set_boot_name_command = "parted " + boot_device + " --script -- name 2 grub"
#run_command(set_boot_name_command)
#command = "mkfs.ext4 " + boot_device + "2"
#run_command(command)

#set_boot_on_command = "parted " + boot_device + " --script -- set 2 boot on"
#run_command(set_boot_on_command)
#root_partition_boot_flag_command = "parted " + boot_device + " --script -- set 2 boot on"
#run_command(root_partition_boot_flag_command)
