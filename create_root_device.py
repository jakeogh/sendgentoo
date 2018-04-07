#!/usr/bin/env python3
import os
import sys
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from write_gpt import write_gpt
from write_sysfs_partition import write_sysfs_partition
from kcl.printops import eprint
from gentoo_setup_globals import RAID_LIST

def create_root_device(devices, partition_table, filesystem, force, exclusive, raid, raid_group_size, pool_name=False):
    eprint("installing gentoo on root devices:", ' '.join(devices), '(' + partition_table + ')', '(' + filesystem + ')', '(', pool_name, ')')
    for device in devices:
        assert not device[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    if not force:
        eprint("THIS WILL DESTROY ALL DATA ON", ' '.join(devices), "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        eprint("Sleeping 5 seconds")
        time.sleep(5)

    if exclusive:
        if filesystem != 'zfs':
            destroy_block_device_head_and_tail(device=device, force=True)
            write_gpt(device, no_wipe=True, force=force, no_backup=False) #zfs does this on it's own, feed it a blank disk
    else:
        pass

    if pool_name:
        write_sysfs_partition(devices=devices, force=True, exclusive=exclusive, filesystem=filesystem, raid=raid, pool_name=pool_name, raid_group_size=raid_group_size)
    else:
        write_sysfs_partition(devices=devices, force=True, exclusive=exclusive, filesystem=filesystem, raid=raid, raid_group_size=raid_group_size)

@click.command()
@click.argument('devices',         required=True, nargs=-1)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force',           is_flag=True,  required=False)
@click.option('--exclusive',       is_flag=True,  required=False)
@click.option('--raid',            is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size', is_flag=False, required=True, type=int)
@click.option('--pool-name',       is_flag=False, required=False, type=str)
def main(devices, partition_table, filesystem, force, exclusive, raid, pool_name):
    create_root_device(devices=devices, partition_table=partition_table, filesystem=filesystem, force=force, exclusive=exclusive, raid=raid, raid_group_size=raid_group_size, pool_name=pool_name)

if __name__ == '__main__':
    main()
    quit(0)

