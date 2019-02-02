#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import ceprint
from .format_partition import format_partition
from kcl.deviceops import warn

def write_efi_partition(device, force, start, end, partition_number):
    ceprint("creating efi partition on device:", device, "partition_number:", partition_number, "start:", start, "end:", end)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        warn((device,))

    #output = run_command("parted " + device + " --align optimal --script -- mkpart primary " + start + ' ' + end)
    output = run_command("parted --align minimal " + device + " --script -- mkpart primary " + start + ' ' + end, verbose=True)
    run_command("parted " + device + " --script -- name " + partition_number + " EFI")
    run_command("parted " + device + " --script -- set " + partition_number + " boot on")

    fat16_partition_device = device+partition_number
    if not path_is_block_special(fat16_partition_device):
        ceprint("fat16_partition_device", fat16_partition_device, "is not block special yet, waiting a second.")
        time.sleep(1)

    format_partition(device=fat16_partition_device, partition_type='fat16', force=True)

    # 127488 /mnt/sdb2/EFI/BOOT/BOOTX64.EFI


@click.command()
@click.option('--device', is_flag=False, required=True)
#@click.option('--start', is_flag=False, required=False, type=str, default='2MiB')
#@click.option('--end',   is_flag=False, required=False, type=str, default='3MiB') #was 100MiB
@click.option('--start',  is_flag=False, required=True, type=str)
@click.option('--end',    is_flag=False, required=True, type=str)
@click.option('--partition-number',    is_flag=False, required=True, type=str)
@click.option('--force',  is_flag=True,  required=False)
def main(device, start, end, partition_number, force):
    write_efi_partition(device=device, start=start, end=end, force=force, partition_number=partition_number)


if __name__ == '__main__':
    main()
