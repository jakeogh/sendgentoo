#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import ceprint

def format_partition(device, partition_type, force):
    ceprint("formatting", partition_type, "partition on:", device)
    assert device[-1].isdigit()
    # oddly, this failed on '/dev/sda2', maybe the kernel was not done
    # digesting the previous table change? (using fat16)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        ceprint("THIS WILL DESTROY ALL DATA ON:", device,
                "_REMOVE_ HARD DRIVES (and USB devices) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Type YES to proceed with deleting all of your important data: ")
        if answer != 'YES':
            quit(1)
        ceprint("Sleeping 5 seconds")
        time.sleep(5)

    if partition_type == 'fat16':
        run_command("mkfs.fat -F16 -s2 " + device)
    elif partition_type == 'fat32':
        run_command("mkfs.fat -F32 -s2 " + device)
    else:
        assert False

    # 127488 /mnt/sdb2/EFI/BOOT/BOOTX64.EFI


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--type', "partition_type", is_flag=False, required=True, type=click.Choice(['fat16', 'fat32']))
@click.option('--force', is_flag=True, required=False)
def main(device, partition_type, force):
    format_partition(device=device, partition_type=partition_type, force=force)


if __name__ == '__main__':
    main()
