#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import eprint
from .write_zfs_root_filesystem_on_devices import write_zfs_root_filesystem_on_devices
from .setup_globals import RAID_LIST
from .warn import warn


def write_sysfs_partition(devices, force, exclusive, filesystem, raid, raid_group_size, pool_name=False):
    eprint("creating sysfs partition on:", devices)

    if filesystem == 'zfs':
        assert pool_name

    for device in devices:
        assert not device[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    if not force:
        warn(devices)

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
        write_zfs_root_filesystem_on_devices(devices=devices, force=True, raid=raid, raid_group_size=raid_group_size, pool_name=pool_name)
    else:
        eprint("unknown filesystem:", filesystem)
        quit(1)
@click.command()
@click.argument('devices',      required=True, nargs=-1)
@click.option('--filesystem', is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force',      is_flag=True,  required=False)
@click.option('--exclusive',  is_flag=True,  required=False)
@click.option('--raid',       is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size',       is_flag=False, required=True, type=int)
@click.option('--pool-name',  is_flag=False, required=False, type=str)
def main(devices, filesystem, force, exclusive, raid, raid_group_size, pool_name):
    write_sysfs_partition(devices=devices, filesystem=filesystem, force=force, exclusive=exclusive, raid=raid, raid_group_size=raid_group_size, pool_name=pool_name)

if __name__ == '__main__':
    main()
    quit(0)

#set_boot_on_command = "parted " + device + " --script -- set 2 boot on"
#run_command(set_boot_on_command)
#root_partition_boot_flag_command = "parted " + device + " --script -- set 2 boot on"
#run_command(root_partition_boot_flag_command)

