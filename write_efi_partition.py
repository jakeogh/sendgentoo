#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import ceprint
from format_fat16_partition import format_fat16_partition


def write_efi_partition(device, force, start, end, partition_number):
    ceprint("creating efi partition on device:", device, "partition_number:", partition_number, "start:", start, "end:", end)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        ceprint("THIS WILL DESTROY ALL DATA ON:", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        ceprint("Sleeping 5 seconds")
        time.sleep(5)

    #output = run_command("parted " + device + " --align optimal --script -- mkpart primary " + start + ' ' + end)
    output = run_command("parted --align minimal " + device + " --script -- mkpart primary " + start + ' ' + end, verbose=True)
    run_command("parted " + device + " --script -- name " + partition_number + " EFI")
    run_command("parted " + device + " --script -- set " + partition_number + " boot on")

    fat16_partition_device = device+partition_number
    if not path_is_block_special(fat16_partition_device):
        ceprint("fat16_partition_device", fat16_partition_device, "is not block special yet, waiting a second.")
        time.sleep(1)

    format_fat16_partition(device=fat16_partition_device, force=True)

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
